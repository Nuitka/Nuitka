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
""" Generators for Python C/API.

This is the actual C++ code generator. It has methods and should be the only place to know
what C++ is like. Ideally it would be possible to replace the target language by changing
this one and the templates, and otherwise nothing else.

"""


from .__past__ import cpickle
import pickle

from .Identifiers import Identifier, ModuleVariableIdentifier, LocalVariableIdentifier, TempVariableIdentifier, getCodeTemporaryRefs, getCodeExportRefs

from . import (
    PythonOperators,
    CppRawStrings,
    CodeTemplates,
    Variables,
    # TODO: Constants should have a separate module.
    Contexts,
    Options
)

from logging import warning

def _indentedCode( codes, count ):
    return "\n".join( " " * count + line if (line and not line.startswith( "#" )) else line for line in codes )

def _indented( codes, level = 1 ):
    if type( codes ) == str:
        codes = codes.split( "\n" )

    return _indentedCode( codes, level * 4 )

def getConstantHandle( context, constant ):
    return context.getConstantHandle( constant )

def getConstantCode( context, constant ):
    constant_identifier = context.getConstantHandle(
        constant = constant
    )

    return constant_identifier.getCode()

def getConstantAccess( context, constant ):
    if type( constant ) is dict:
        return Identifier(
            "PyDict_Copy( %s )" % getConstantCode(
                constant = constant,
                context = context
            ),
            1
        )
    elif type( constant ) is set:
        return Identifier(
            "PySet_New( %s )" % getConstantCode(
                constant = constant,
                context = context
            ),
            1
        )
    elif type( constant ) is list:
        return Identifier(
            "LIST_COPY( %s )" % getConstantCode(
                constant = constant,
                context = context
            ),
            1
        )
    else:
        return context.getConstantHandle(
            constant = constant
        )

def getVariableHandle( context, variable ):
    assert isinstance( variable, Variables.Variable ), variable

    var_name = variable.getName()

    if variable.isLocalVariable() or variable.isClassVariable():
        return context.getLocalHandle(
            var_name = var_name
        )
    elif variable.isClosureReference():
        return context.getClosureHandle(
            var_name = var_name
        )
    elif variable.isMaybeLocalVariable():
        context.addGlobalVariableNameUsage( var_name )

        return context.getMaybeLocalHandle(
            var_name = var_name
        )
    elif variable.isModuleVariable():
        context.addGlobalVariableNameUsage(
            var_name = var_name
        )

        return ModuleVariableIdentifier(
            var_name         = var_name,
            module_code_name = context.getModuleCodeName()
        )

    else:
        assert False, variable

def getVariableCode( context, variable ):
    var_identifier = getVariableHandle(
        context  = context,
        variable = variable
    )

    return var_identifier.getCode()


def getReturnCode( identifier ):
    if identifier is not None:
        return "return %s;" % identifier.getCodeExportRef()
    else:
        return "return;"

def getYieldCode( identifier ):
    return Identifier(
        "YIELD_VALUE( generator, %s )" % identifier.getCodeExportRef(),
        0
    )

def getYieldTerminatorCode():
    return "throw ReturnException();"

def getSequenceCreationCode( sequence_kind, element_identifiers ):
    assert sequence_kind in ( "tuple", "list" )

    # Disallow building the empty tuple with this assertion, we want users to not let
    # us here optimize it away.
    assert sequence_kind != "list" or element_identifiers

    if sequence_kind == "tuple":
        arg_codes = getCodeTemporaryRefs( element_identifiers )
    else:
        arg_codes = getCodeExportRefs( element_identifiers )

    return Identifier(
        "MAKE_%(sequence_kind)s( %(args)s )" % {
            "sequence_kind" : sequence_kind.upper(),
            "args"          : ", ".join( reversed( arg_codes ) )
        },
        1
    )

def getDictionaryCreationCode( keys, values ):
    key_codes = getCodeTemporaryRefs( keys )
    value_codes = getCodeTemporaryRefs( values )

    arg_codes = []

    for key_code, value_code in zip( key_codes, value_codes ):
        arg_codes.append( value_code )
        arg_codes.append( key_code )

    return Identifier(
        "MAKE_DICT( %s )" % ( ", ".join( reversed( arg_codes ) ) ),
        1
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

    return package_var_identifier.getCode()

def getEmptyImportListCode():
    return Identifier( "NULL", 0 )

def getImportModuleCode( context, module_name, import_name, import_list ):
    return Identifier(
        "IMPORT_MODULE( %s, %s, &%s, %s )" % (
            getConstantCode(
                constant = module_name,
                context  = context
            ),
            getConstantCode(
                constant = import_name,
                context  = context
            ),
            getPackageVariableCode(
                context = context
            ),
            import_list.getCodeTemporaryRef()
        ),
        1
    )

def getImportEmbeddedCode( context, module_name, import_name ):
    return Identifier(
        "IMPORT_EMBEDDED_MODULE( %s, %s )" % (
            getConstantCode(
                constant = module_name,
                context  = context
            ),
            getConstantCode(
                constant = import_name,
                context  = context
            )
        ),
        1
    )

def getImportFromStarCode( context, module_name, embedded ):
    if embedded:
        module_code = getImportEmbeddedCode(
            context     = context,
            module_name = module_name,
            import_name = module_name
        )
    else:
        module_code = getImportModuleCode(
            context     = context,
            module_name = module_name,
            import_name = module_name,
            import_list = getEmptyImportListCode()
        )

    if not context.hasLocalsDict():
        return "IMPORT_MODULE_STAR( %s, true, %s, %s );" % (
            getModuleAccessCode( context = context ),
            getConstantCode(
                constant = module_name,
                context  = context
            ),
            module_code.getCodeTemporaryRef()
        )
    else:
        return "IMPORT_MODULE_STAR( locals_dict.asObject(), false, %s, %s );" % (
            getConstantCode(
                constant = module_name,
                context  = context
            ),
            module_code.getCodeTemporaryRef()
        )


def getImportFromModuleTempIdentifier():
    return Identifier( "module_temp.asObject()", 0 )

def getImportFromCode( context, module_name, lookup_code, import_list, embedded, sub_modules ):
    if embedded:
        module_lookup = getImportEmbeddedCode(
            context     = context,
            module_name = module_name,
            import_name = module_name
        )
    else:
        module_lookup = getImportModuleCode(
            context = context,
            module_name = module_name,
            import_name = module_name,
            import_list = getConstantHandle(
                context  = context,
                constant = tuple( import_list )
            )
        )

    module_embedded = [
        getStatementCode(
            getImportEmbeddedCode(
                context     = context,
                module_name = module_name,
                import_name = module_name
            )
        )
        for module_name in
        sub_modules
    ]

    return CodeTemplates.import_from_template % {
        "module_lookup"   : _indented( module_lookup.getCodeExportRef(), 2 ),
        "module_embedded" : _indented( module_embedded ),
        "lookup_code"     : _indented( lookup_code, 2 ),
    }


def getMaxIndexCode():
    return Identifier( "PY_SSIZE_T_MAX", 0 )

def getMinIndexCode():
    return Identifier( "0", 0 )

def getIndexCode( identifier ):
    return Identifier(
        "CONVERT_TO_INDEX( %s )" % identifier.getCodeTemporaryRef(),
        0
    )

def _getFunctionCallNoStarArgsCode( function_identifier, argument_tuple, argument_dictionary ):
    return Identifier(
        "CALL_FUNCTION( %(named_args)s, %(pos_args)s, %(function)s )" % {
            "function"   : function_identifier.getCodeTemporaryRef(),
            "pos_args"   : argument_tuple.getCodeTemporaryRef(),
            "named_args" : argument_dictionary.getCodeTemporaryRef()
        },
        1
    )

def _getFunctionCallListStarArgsCode( function_identifier, argument_tuple, argument_dictionary, star_list_identifier ):
    return Identifier(
        "CALL_FUNCTION_STAR_LIST( %(star_list_arg)s, %(named_args)s, %(pos_args)s, %(function)s )" % {
            "function"   : function_identifier.getCodeTemporaryRef(),
            "pos_args"   : argument_tuple.getCodeTemporaryRef(),
            "named_args" : argument_dictionary.getCodeTemporaryRef(),
            "star_list_arg" : star_list_identifier.getCodeTemporaryRef()
        },
        1
    )

def _getFunctionCallDictStarArgsCode( function_identifier, argument_tuple, argument_dictionary, star_dict_identifier ):
    return Identifier(
        "CALL_FUNCTION_STAR_DICT( %(star_dict_arg)s, %(named_args)s, %(pos_args)s, %(function)s )" % {
            "function"      : function_identifier.getCodeTemporaryRef(),
            "pos_args"      : argument_tuple.getCodeTemporaryRef(),
            "named_args"    : argument_dictionary.getCodeTemporaryRef(),
            "star_dict_arg" : star_dict_identifier.getCodeTemporaryRef()
        },
        1
    )

def _getFunctionCallBothStarArgsCode( function_identifier, argument_tuple, argument_dictionary, star_list_identifier, star_dict_identifier ):
    return Identifier(
        "CALL_FUNCTION_STAR_BOTH( %(star_dict_arg)s, %(star_list_arg)s, %(named_args)s, %(pos_args)s, %(function)s )" % {
            "function"      : function_identifier.getCodeTemporaryRef(),
            "pos_args"      : argument_tuple.getCodeTemporaryRef(),
            "named_args"    : argument_dictionary.getCodeTemporaryRef(),
            "star_list_arg" : star_list_identifier.getCodeTemporaryRef(),
            "star_dict_arg" : star_dict_identifier.getCodeTemporaryRef()
        },
        1
    )


def getFunctionCallCode( function_identifier, argument_tuple, argument_dictionary, star_list_identifier, star_dict_identifier ):
    if False and star_dict_identifier is not None and argument_dictionary.getCode() == "_python_dict_empty":
        # TODO: Should check for Dict and probably make a copy from the potential
        # mapping it is, otherwise this optimization is not valid.
        argument_dictionary  = star_dict_identifier
        star_dict_identifier = None

    if star_dict_identifier is None:
        if argument_dictionary.getCode() == "_python_dict_empty":
            argument_dictionary = Identifier( "NULL", 0 )

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
        result += "PyObjectTemporary %s( %s );\n" % (
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

def getSubscriptLookupCode( subscript, source ):
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

    return "{\n%s\n}" % _indented( codes )

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
    elif len( identifiers ) == 2:
        return Identifier(
            "BINARY_OPERATION( %s, %s, %s )" % (
                PythonOperators.binary_operator_codes[ operator ],
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif len( identifiers ) == 1:
        return Identifier(
            "UNARY_OPERATION( %s, %s )" % (
                PythonOperators.unary_operator_codes[ operator ],
                identifier_refs[0]
            ),
            1
        )
    else:
        assert False, (operator, identifiers)

def getPrintCode( newline, identifiers, target_file ):
    args = [
        "true" if newline else "false",
        target_file.getCodeTemporaryRef() if target_file is not None else "NULL"
    ]

    args += getCodeTemporaryRefs( identifiers )

    return "PRINT_ITEMS( %s );" % ( ", ".join( args ) )


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

def getContractionCallCode( is_generator, contraction_identifier, contraction_iterated, closure_var_codes ):
    args = [ contraction_iterated.getCodeTemporaryRef() ] + closure_var_codes

    if is_generator:
        prefix = "MAKE_FUNCTION_"
    else:
        prefix = ""

    return Identifier(
        "%s%s( %s )" % (
            prefix,
            contraction_identifier,
            ", ".join( args )
        ),
        1
    )

def getLambdaExpressionReferenceCode( context, lambda_expression, default_values ):
    return getFunctionCreationCode(
        function       = lambda_expression,
        default_values = default_values,
        decorators     = (),
        context        = context
    )

def getConditionalExpressionCode( condition, codes_no, codes_yes ):
    if codes_yes.getCheapRefCount() == codes_no.getCheapRefCount():
        if codes_yes.getCheapRefCount == 0:
            return Identifier( "( %s ? %s : %s )" % ( condition.getCode(), codes_yes.getCodeTemporaryRef(), codes_no.getCodeTemporaryRef() ), 0 )
        else:
            return Identifier( "( %s ? %s : %s )" % ( condition.getCode(), codes_yes.getCodeExportRef(), codes_no.getCodeExportRef() ), 1 )
    else:
        return Identifier( "( %s ? %s : %s )" % ( condition.getCode(), codes_yes.getCodeExportRef(), codes_no.getCodeExportRef() ), 1 )

def getGeneratorExpressionCreationCode( context, iterated_identifier, generator_expression ):
    args =  [ getIteratorCreationCode( iterated = iterated_identifier ).getCodeExportRef() ]

    args += getClosureVariableProvisionCode(
        context           = context,
        closure_variables = generator_expression.getClosureVariables()
    )

    return Identifier(
        "MAKE_FUNCTION_%s( %s )" % (
            generator_expression.identifier,
            ", ".join( args )
        ),
        1
    )

def getFunctionCreationCode( context, function, decorators, default_values ):
    args = [ identifier.getCodeTemporaryRef() for identifier in decorators ]

    args += [ identifier.getCodeExportRef() for identifier in default_values ]

    args += getClosureVariableProvisionCode(
        context           = context,
        closure_variables = function.getClosureVariables()
    )

    return Identifier(
        "MAKE_FUNCTION_%s( %s )" % (
            function.getCodeName(),
            ", ".join( args )
        ),
        1
    )

def getBranchCode( conditions, branches_codes ):
    result = ""

    keyword = "if"

    for condition, branch_codes in zip( conditions, branches_codes ):
        if condition is not None:
            result += "%s ( %s )\n" % ( keyword, condition.getCode() )
            result += getBlockCode( _indented( branch_codes ) )

            keyword = "else if"

    if len( conditions ) == len( branches_codes ) - 1 and branches_codes[-1]:
        result += "else\n"
        result += getBlockCode( _indented( branches_codes[-1] ) )

    result = result.rstrip()

    return result

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
    # assert len( comparators ) == 1

    if len( comparators ) == 1:
        comparator = comparators[0]

        left, right = operands

        if comparator in PythonOperators.normal_comparison_operators:
            py_api = PythonOperators.normal_comparison_operators[ comparator ]

            if py_api.startswith( "SEQUENCE_CONTAINS" ):
                left, right = right, left

                reference = 0
            else:
                reference = 1

            comparison = Identifier(
                "%s( %s, %s )" % (
                    py_api,
                    left.getCodeTemporaryRef(),
                    right.getCodeTemporaryRef()
                ),
                reference
            )
        elif comparator in PythonOperators.rich_comparison_codes:
            comparison = Identifier(
                "RICH_COMPARE( %s, %s, %s )" % (
                    PythonOperators.rich_comparison_codes[ comparator ],
                    right.getCodeTemporaryRef(),
                    left.getCodeTemporaryRef()
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
            if comparator in PythonOperators.normal_comparison_operators:
                assert False, comparator
            elif comparator in PythonOperators.rich_comparison_codes:
                chunk = "RICH_COMPARE_BOOL( %s, %s, %s )" % (
                    PythonOperators.rich_comparison_codes[ comparator ],
                    right_tmp,
                    left_tmp.getCodeTemporaryRef()
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
    # assert len( comparators ) == 1

    if len( comparators ) == 1:
        comparator = comparators[0]

        left, right = operands

        if comparator in PythonOperators.normal_comparison_operators:
            py_api = PythonOperators.normal_comparison_operators[ comparator ]

            if py_api.startswith( "SEQUENCE_CONTAINS" ):
                left, right = right, left

                reference = 0
            else:
                reference = 1

            comparison = Identifier(
                "%s_BOOL( %s, %s )" % (
                    py_api,
                    left.getCodeTemporaryRef(),
                    right.getCodeTemporaryRef()
                ),
                reference
            )
        elif comparator in PythonOperators.rich_comparison_codes:
            comparison = Identifier(
                "RICH_COMPARE_BOOL( %s, %s, %s )" % (
                    PythonOperators.rich_comparison_codes[ comparator ],
                    right.getCodeTemporaryRef(),
                    left.getCodeTemporaryRef()
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

                right_tmp = "(%s = %s)" % (
                    temp_storage_var.getCode(),
                    right_tmp
                )

            if comparator in PythonOperators.normal_comparison_operators:
                assert False, comparator
            elif comparator in PythonOperators.rich_comparison_codes:
                chunk = "RICH_COMPARE_BOOL( %s, %s, %s )" % (
                    PythonOperators.rich_comparison_codes[ comparator ],
                    right_tmp,
                    left_tmp.getCodeTemporaryRef()
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

def getSliceAssignmentCode( target, lower, upper, identifier  ):
    return "SET_SLICE( %s, %s, %s, %s );" % (
        target.getCodeTemporaryRef(),
        lower.getCodeTemporaryRef(),
        upper.getCodeTemporaryRef(),
        identifier.getCodeTemporaryRef()
    )

def getSliceDelCode( target, lower, upper ):
    return "DEL_SLICE( %s, %s, %s );" % (
        target.getCodeTemporaryRef(),
        lower.getCodeTemporaryRef() if lower is not None else "Py_None",
        upper.getCodeTemporaryRef() if upper is not None else "Py_None"
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

    return CodeTemplates.with_template % {
        "assign"              : _indented( assign_codes ),
        "body"                : _indented( body_codes, 2 ),
        "source"              : source_identifier.getCodeExportRef(),
        "manager"             : with_manager_identifier.getCode(),
        "value"               : with_value_identifier.getCode(),
        "with_count"          : context.with_count,
        "module_identifier"   : getModuleAccessCode( context = context ),
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
        TempVariableIdentifier( "itertemp_%d" % for_count )
    )

def getForLoopCode( context, line_number_code, iterator, iter_name, iter_value, iter_object, loop_var_code, loop_body_codes, loop_else_codes, needs_exceptions ):
    for_loop_template = CodeTemplates.getForLoopTemplate(
        needs_exceptions = needs_exceptions,
        has_else_codes   = loop_else_codes
    )

    indicator_name = "_python_for_loop_indicator_%d" % context.allocateForLoopNumber()

    return for_loop_template % {
        "body"                     : _indented( loop_body_codes, 2 ),
        "else_codes"               : _indented( loop_else_codes ),
        "iterator"                 : iterator.getCodeExportRef(),
        "line_number_code"         : line_number_code,
        "loop_iter_identifier"     : iter_name,
        "loop_value_identifier"    : iter_value,
        "loop_object_identifier"   : iter_object.getCode(),
        "loop_var_assignment_code" : _indented( loop_var_code, 3 ),
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
        "loop_body_codes" : _indented( loop_body_codes ),
        "loop_else_codes" : _indented( loop_else_codes ),
        "indicator_name"  : indicator_name
    }

def getAssignmentCode( context, variable, identifier ):
    assert isinstance( variable, Variables.Variable ), variable

    if variable.isModuleVariable():
        var_name = variable.getName()

        context.addGlobalVariableNameUsage( var_name )

        return "_mvar_%s_%s.assign( %s );" % (
            context.getModuleCodeName(),
            var_name,
            identifier.getCodeExportRef()
        )
    elif variable.isMaybeLocalVariable():
        return "SET_SUBSCRIPT( locals_dict.asObject(), %s, %s );" % (
            getConstantCode(
                context  = context,
                constant = variable.getName(),

            ),
            identifier.getCodeExportRef()
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
        subscribed.getCodeTemporaryRef(),
        subscript.getCodeTemporaryRef(),
        identifier.getCodeTemporaryRef()
    )

def getSubscriptDelCode( subscribed, subscript ):
    return "DEL_SUBSCRIPT( %s, %s );" % (
        subscribed.getCodeTemporaryRef(),
        subscript.getCodeTemporaryRef()
    )

def _getInplaceOperationCode( operator, operand1, operand2 ):
    operator = PythonOperators.inplace_operator_codes[ operator ]

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
        "assignment_code" : getAssignmentCode(
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
        "tried_code" : _indented( code_tried ),
        "final_code" : _indented( code_final, 0 )
    }

def getTryExceptCode( context, code_tried, exception_identifiers, exception_assignments, catcher_codes, else_code ):
    exception_code = []

    cond_keyword = "if"

    for exception_identifier, exception_assignment, handler_code in zip( exception_identifiers, exception_assignments, catcher_codes ):
        if exception_identifier is not None:
            exception_code.append(
                "%s (_exception.matches(%s))" % (
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
            exception_code.append( _indented( exception_assignment, 1 ) )

        exception_code += _indented( handler_code, 1 ).split("\n")
        exception_code.append( "}" )

        cond_keyword = "else if"

    exception_code += [ "else", "{", "    throw;", "}" ]

    tb_making = getTracebackMakingIdentifier( context, "_exception.getLine()" ).getCodeExportRef()

    if else_code is not None:
        return CodeTemplates.try_except_else_template % {
            "tried_code"     : _indented( code_tried ),
            "exception_code" : _indented( exception_code ),
            "else_code"      : _indented( else_code ),
            "tb_making"      : tb_making,
            "except_count"   : context.allocateTryNumber()
        }
    else:
        return CodeTemplates.try_except_template % {
            "tried_code"     : _indented( code_tried ),
            "exception_code" : _indented( exception_code ),
            "tb_making"      : tb_making,
        }


def getRaiseExceptionCode( exception_type_identifier, exception_value_identifier, exception_tb_identifier, exception_tb_maker ):
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
        return "throw;"
    else:
        return "traceback = true; RERAISE_EXCEPTION();"

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

def _getLocalVariableList( context, provider ):
    if provider.isFunctionBody():
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
        if not variable.isModuleVariable():
            key_identifier = getConstantHandle(
                context = context,
                constant = variable.getName()
            )

            var_assign_code = getAssignmentCode(
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


def getEvalCode( context, exec_code, globals_identifier, locals_identifier, future_flags, provider ):
    if context.getParent() is None:
        return Identifier(
            CodeTemplates.eval_global_template % {
                "globals_identifier"      : globals_identifier.getCodeTemporaryRef(),
                "locals_identifier"       : locals_identifier.getCodeTemporaryRef(),
                "make_globals_identifier" : getLoadGlobalsCode(
                    context = context
                ).getCodeExportRef(),
                "source_identifier"       : exec_code.getCodeTemporaryRef(),
                "filename_identifier"     : getConstantCode(
                    constant = "<string>",
                    context  = context
                ),
                "mode_identifier"         : getConstantCode(
                    constant = "eval",
                    context  = context
                ),
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
                "filename_identifier"     : getConstantCode(
                    constant = "<string>",
                    context  = context
                ),
                "mode_identifier"         : getConstantCode(
                    constant = "eval",
                    context  = context
                ),
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
            "filename_identifier"     : getConstantCode(
                constant = "<string>",
                context = context
            ),
            # TODO: Move to the outside, and make using the real source reference an
            # option.
            "mode_identifier"         : getConstantCode(
                constant = "exec",
                context  = context
            ),
            "future_flags"            : future_flags,
            "store_locals_code"       : _indented(
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

def getModuleAccessCode( context ):
    return Identifier( "_module_%s" % context.getModuleCodeName(), 0 ).getCode()

def getFrameMakingIdentifier( context, line ):
    return Identifier(
        "MAKE_FRAME( %(module_identifier)s, %(module_filename_identifier)s, %(code_identifier)s, %(line)s )" % {
            "module_identifier"          : getModuleAccessCode(
                context = context
            ),
            "module_filename_identifier" : getConstantCode(
                context = context,
                constant = context.getTracebackFilename()
            ),
            "code_identifier"            : getConstantCode(
                context = context,
                constant = context.getTracebackName()
            ),
            "line"                       : line
        },
        1
    )

def getTracebackMakingIdentifier( context, line ):
    return Identifier(
        "MAKE_TRACEBACK( %s, %s )" % (
            getFrameMakingIdentifier( context = context, line = line ).getCodeTemporaryRef(),
            line
        ),
        1
    )

def getModuleIdentifier( module_name ):
    return module_name.replace( ".", "__" ).replace( "-", "_" )

def getPackageIdentifier( module_name ):
    return module_name.replace( ".", "__" )

def getModuleCode( context, stand_alone, module_name, package_name, codes, doc_identifier, path_identifier, filename_identifier ):
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
            "static PyObjectGlobalVariable _mvar_%s_%s( &_module_%s, &%s );" % (
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
    context.getConstantHandle( constant = "<module>" )

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
            "package_name_identifier" : getConstantCode(
                constant = package_name,
                context  = context
            ),
            "package_identifier"      : getPackageIdentifier( package_name )
        }

    if stand_alone:
        header = CodeTemplates.global_copyright % {
            "name" : module_name
        }
    else:
        header = CodeTemplates.module_header % {
            "name" : module_name,
        }

    module_code = CodeTemplates.module_body_template % {
        "module_name"           : module_name,
        "module_identifier"     : module_identifier,
        "module_functions_decl" : functions_decl,
        "module_functions_code" : functions_code,
        "module_globals"        : module_globals,
        "module_inits"          : module_inits,
        "filename_identifier"   : filename_identifier.getCode(),
        "module_code"           : _indented( codes, 2 ),
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

def getMainCode( codes, other_modules ):
    module_inittab = []

    for other_module in other_modules:
        module_name = other_module.getFullName()

        module_inittab.append (
            CodeTemplates.module_inittab_entry % {
                "module_name"       : module_name,
                "module_identifier" : getModuleIdentifier( module_name ),
            }
        )

    main_code = CodeTemplates.main_program % {
        "module_inittab" : _indented( sorted( module_inittab ) )
    }

    return codes + main_code


def getFunctionsCode( context ):
    result = ""

    for contraction_info in sorted( context.getContractionsCodes(), key = lambda x : x[0].getCodeName() ):
        contraction, contraction_identifier, contraction_context, loop_var_codes, contraction_code, contraction_conditions, contraction_iterateds = contraction_info

        if contraction.isExpressionGeneratorBuilder():
            result += getGeneratorExpressionCode(
                context              = context,
                generator            = contraction,
                generator_identifier = contraction_identifier,
                generator_code       = contraction_code,
                generator_conditions = contraction_conditions,
                generator_iterateds  = contraction_iterateds,
                loop_var_codes       = loop_var_codes
            )
        else:
            result += getContractionCode(
                contraction            = contraction,
                contraction_context    = contraction_context,
                contraction_identifier = contraction_identifier,
                contraction_code       = contraction_code,
                contraction_conditions = contraction_conditions,
                contraction_iterateds  = contraction_iterateds,
                loop_var_codes         = loop_var_codes
            )


    functions_infos = context.getFunctionsCodes()

    for function, function_context, function_codes in sorted( functions_infos, key = lambda x : x[0].getCodeName() ):
        result += getFunctionCode(
            context        = function_context,
            function       = function,
            function_codes = function_codes
        )

    classes_infos = context.getClassesCodes()

    for class_def, ( class_context, class_codes ) in sorted( classes_infos.items(), key = lambda x : x[0].getCodeName() ):
        result += getClassCode(
            context     = class_context,
            class_def   = class_def,
            class_codes = class_codes
        )

    for lambda_def, lambda_codes, lambda_context in sorted( context.getLambdasCodes(), key = lambda x : x[0].getCodeName() ):
        result += getLambdaCode(
            context      = lambda_context,
            lambda_def   = lambda_def,
            lambda_codes = lambda_codes
        )

    return result

def getFunctionsDecl( context ):
    result = ""

    for contraction_info in sorted( context.getContractionsCodes(), key = lambda x : x[0].getCodeName() ):
        contraction, contraction_identifier, _contraction_context, _loop_var_code, _contraction_code, _contraction_conditions, _contraction_iterateds = contraction_info
        if contraction.isExpressionGeneratorBuilder():
            result += getGeneratorExpressionDecl(
                generator_expression = contraction,
                generator_identifier = contraction_identifier
            )
        else:
            result += getContractionDecl(
                contraction            = contraction,
                contraction_identifier = contraction_identifier
            )

    functions_infos = context.getFunctionsCodes()

    for function, _function_context, _function_codes in sorted( functions_infos, key = lambda x : x[0].getCodeName() ):
        result += getFunctionDecl( function = function )

    classes_infos = context.getClassesCodes()

    for class_def, ( _class_context, _class_codes ) in sorted( classes_infos.items(), key = lambda x : x[0].getCodeName() ):
        result += getClassDecl(
            class_def = class_def
        )

    for lambda_def, _lambda_code, _lambda_context in sorted( context.getLambdasCodes(), key = lambda x : x[0].getCodeName() ):
        result += getLambdaDecl(
            lambda_def = lambda_def
        )

    return result

def _getContractionParameters( contraction ):
    contraction_parameters = [ "PyObject *iterated" ]

    for variable in contraction.getClosureVariables():
        assert variable.isClosureReference()

        contraction_parameters.append(
            _getClosureVariableDecl(
                variable     = variable
            )
        )

    return contraction_parameters

def getContractionDecl( contraction, contraction_identifier ):
    contraction_parameters = _getContractionParameters(
        contraction = contraction
    )

    return CodeTemplates.contraction_decl_template % {
       "contraction_identifier" : contraction_identifier,
       "contraction_parameters" : ", ".join( contraction_parameters )
    }

def getContractionCode( contraction, contraction_context, contraction_identifier, loop_var_codes, contraction_code, contraction_conditions, contraction_iterateds ):
    contraction_parameters = _getContractionParameters(
        contraction = contraction
    )

    if contraction.isListContractionBuilder():
        contraction_decl_template = CodeTemplates.list_contration_var_decl
        contraction_loop = CodeTemplates.list_contraction_loop_production % {
            "contraction_body" : contraction_code.getCodeTemporaryRef(),
        }
    elif contraction.isSetContractionBuilder():
        contraction_decl_template = CodeTemplates.set_contration_var_decl
        contraction_loop = CodeTemplates.set_contraction_loop_production % {
            "contraction_body" : contraction_code.getCodeTemporaryRef(),
        }

    elif contraction.isDictContractionBuilder():
        contraction_decl_template = CodeTemplates.dict_contration_var_decl
        contraction_loop = CodeTemplates.dict_contraction_loop_production % {
            "key_identifier" : contraction_code[0].getCodeTemporaryRef(),
            "value_identifier" : contraction_code[1].getCodeTemporaryRef()
        }

    else:
        assert False, contraction

    local_var_decl = []

    for variable in contraction.getProvidedVariables():
        if not variable.isClosureReference() and not variable.isModuleVariable():
            local_var_decl.append(
                _getLocalVariableInitCode(
                    context    = contraction_context,
                    variable   = variable,
                    in_context = False
                )
            )


    contraction_var_decl = contraction_decl_template % {
        "local_var_decl" : _indented( local_var_decl )
    }

    contraction_iterateds.insert( 0, Identifier( "iterated", 0 ) )

    for count, ( contraction_condition, contraction_iterated, loop_var_code ) in enumerate ( reversed( list( zip( contraction_conditions, contraction_iterateds, loop_var_codes ) ) ) ):
        contraction_loop = CodeTemplates.contraction_loop_iterated % {
            "contraction_loop"         : contraction_loop,
            "iter_count"               : len( loop_var_codes ) - count,
            "iterated"                 : contraction_iterated.getCodeTemporaryRef(),
            "loop_var_assignment_code" : loop_var_code,
            "contraction_condition"    : contraction_condition.getCode()
        }

    return CodeTemplates.contraction_code_template % {
        "contraction_identifier" : contraction_identifier,
        "contraction_parameters" : ", ".join( contraction_parameters ),
        "contraction_body"       : contraction_loop,
        "contraction_var_decl"   : _indented( contraction_var_decl.split( "\n" ) )
    }

def getContractionIterValueIdentifier( context, index ):
    if not context.isGeneratorExpression():
        return Identifier( "_python_contraction_iter_value_%d" % index, 0 )
    else:
        return Identifier( "_python_genexpr_iter_value", 0 )

def getGeneratorExpressionDecl( generator_expression, generator_identifier ):
    return _getFunctionDecl(
        function_identifier = generator_identifier,
        parameters          = None,
        closure_variables   = generator_expression.getClosureVariables(),
        decorators          = (),
        is_generator        = True
    )

def _getFunctionCreationArgs( decorators, parameters, closure_variables, is_generator ):
    if decorators:
        result = [
            "PyObject *decorator_%d" % ( d + 1 )
            for d in
            range( len( decorators ) )
        ]
    else:
        result = []

    if is_generator:
        result += [ "PyObject *iterator" ]

    if parameters is not None:
        for defaulted_variable in parameters.getDefaultParameterVariables():
            default_par_code_name = _getDefaultParameterCodeName( defaulted_variable )

            result.append( "PyObject *%s" % default_par_code_name )

    for closure_variable in closure_variables:
        result.append( "PyObjectSharedLocalVariable &python_closure_%s" % closure_variable.getName() )

    return ", ".join( result )

def _getFunctionDecl( function_identifier, decorators, parameters, closure_variables, is_generator ):
    return CodeTemplates.function_decl_template % {
        "function_identifier"    : function_identifier,
        "function_creation_args" : _getFunctionCreationArgs(
            decorators        = decorators,
            parameters        = parameters,
            closure_variables = closure_variables,
            is_generator      = is_generator
        )
    }

def _getLocalVariableInitCode( context, variable, init_from = None, needs_no_free = False, in_context = False, shared = False, mangle_name = None ):
    assert not variable.isModuleVariable()

    shared = shared or variable.isShared()

    if shared:
        result = "PyObjectSharedLocalVariable"
    else:
        result = "PyObjectLocalVariable"

    var_name = variable.getName()

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
                    result += ", true"

        result += " )"

    result += ";"

    return result

def _getDefaultParameterCodeName( variable ):
    if variable.isNestedParameterVariable():
        return "default_values_%s" % "_".join( variable.getParameterNames() )
    else:
        return "default_value_%s" % variable.getName()

def _getParameterParsingCode( context, function_name, parameters ):
    function_context_decl = []
    function_context_copy = []
    function_context_free = []

    function_parameter_variables = parameters.getVariables()

    parameter_parsing_code = "\n".join(
        [
            "PyObject *_python_par_" + variable.getName() + " = NULL;"
            for variable in
            parameters.getAllVariables()
        ]
    )

    parameter_release_codes = [
        "Py_XDECREF( _python_par_" + variable.getName() + " );"
        for variable in
        parameters.getAllVariables() if not variable.isNestedParameterVariable()
    ]

    parameter_parsing_code += CodeTemplates.parse_argument_template_take_counts1

    top_level_parameters = parameters.getTopLevelVariables()

    if top_level_parameters and parameters.getDictStarArgVariable() is None:
        parameter_parsing_code += CodeTemplates.parse_argument_template_take_counts2

    if top_level_parameters:
        parameter_parsing_code += CodeTemplates.parse_argument_template_take_counts3 % {
            "top_level_parameter_count" : len( top_level_parameters ),
        }

    if parameters.isEmpty():
        parameter_parsing_code += CodeTemplates.parse_argument_template_refuse_parameters % {
            "function_name" : function_name,
        }
    else:
        if top_level_parameters and parameters.getDictStarArgVariable() is None:
            parameter_parsing_code += CodeTemplates.parse_argument_template_check_dict_parameter_unused_without_star_dict % {
                "function_name"          : function_name,
                "parameter_names_tuple" : getConstantCode(
                    context  = context,
                    constant = tuple(
                        variable.getName()
                        for variable in
                        function_parameter_variables
                    )
                )
            }

        if parameters.getListStarArgVariable() is None:
            check_template = CodeTemplates.parse_argument_template_check_counts_without_list_star_arg
        else:
            check_template = CodeTemplates.parse_argument_template_check_counts_with_list_star_arg

        required_parameter_count = len( top_level_parameters ) - parameters.getDefaultParameterCount()

        parameter_parsing_code += check_template % {
            "function_name"             : function_name,
            "top_level_parameter_count" : len( top_level_parameters ),
            "required_parameter_count"  : required_parameter_count,
        }

    if top_level_parameters:
        parameter_parsing_code += CodeTemplates.parse_argument_usable_count % {
            "top_level_parameter_count" : len( top_level_parameters ),
        }

        for count, variable in enumerate( top_level_parameters ):
            # TODO: These templates really have no sensible names at all.
            if variable.isNestedParameterVariable():
                parse_argument_template2 = CodeTemplates.parse_argument_template2a
            else:
                parse_argument_template2 = CodeTemplates.parse_argument_template2

            parameter_parsing_code += parse_argument_template2 % {
                "parameter_name"     : variable.getName(),
                "parameter_position" : count
            }

    if parameters.getListStarArgVariable() is not None:
        parameter_parsing_code += CodeTemplates.parse_argument_template_copy_list_star_args % {
            "list_star_parameter_name"  : parameters.getListStarArgName(),
            "top_level_parameter_count" : len( top_level_parameters )
        }

    if top_level_parameters:
        parameter_parsing_code += "// Copy given dictionary values to the the respective variables\n"

    if parameters.getDictStarArgVariable() is not None:
        parameter_parsing_code += CodeTemplates.parse_argument_template_dict_star_copy % {
            "dict_star_parameter_name" : parameters.getDictStarArgName(),
        }

        for variable in top_level_parameters:
            if not variable.isNestedParameterVariable():
                parameter_parsing_code += CodeTemplates.parse_argument_template_check_dict_parameter_with_star_dict % {
                    "function_name"            : function_name,
                    "parameter_name"           : variable.getName(),
                    "parameter_name_object"    : getConstantCode(
                        constant = variable.getName(),
                        context  = context
                    ),
                    "dict_star_parameter_name" : parameters.getDictStarArgName(),
                }
    else:
        for variable in top_level_parameters:
            if not variable.isNestedParameterVariable():
                parameter_parsing_code += CodeTemplates.parse_argument_template_check_dict_parameter_without_star_dict % {
                    "function_name"         : function_name,
                    "parameter_name"        : variable.getName(),
                    "parameter_identifier"  : getVariableCode(
                        variable = variable,
                        context = context
                    ),
                    "parameter_name_object" : getConstantCode(
                        constant = variable.getName(),
                        context  = context
                    )
                }

    if parameters.hasDefaultParameters():
        parameter_parsing_code += "// Assign values not given to defaults\n"

        for variable in parameters.getDefaultParameterVariables():
            if not variable.isNestedParameterVariable():
                parameter_parsing_code += CodeTemplates.parse_argument_template_copy_default_value % {
                    "parameter_name"     : variable.getName(),
                    "default_identifier" : context.getDefaultHandle( variable.getName() ).getCode()
                }


    def unPackNestedParameterVariables( variables, recursion ):
        result = ""

        for variable in variables:
            if variable.isNestedParameterVariable():
                if recursion == 1 and variable in parameters.getDefaultParameterVariables():
                    assign_source = Identifier(
                        "_python_par_%s ? _python_par_%s : _python_context->%s" % (
                            variable.getName(),
                            variable.getName(),
                            _getDefaultParameterCodeName( variable )
                        ),
                        0
                    )
                else:
                    assign_source = Identifier(
                        "_python_par_%s" % variable.getName(),
                        0
                    )

                unpack_code = ""

                child_variables = variable.getTopLevelVariables()
                for count, child_variable in enumerate( child_variables ):
                    unpack_code += CodeTemplates.parse_argument_template_nested_argument_assign % {
                        "parameter_name" : child_variable.getName(),
                        "iter_name"      : variable.getName(),
                        "unpack_count"   : count
                    }

                result += CodeTemplates.parse_argument_template_nested_argument_unpack % {
                    "unpack_source_identifier" : assign_source.getCode(),
                    "parameter_name" : variable.getName(),
                    "unpack_code"    : unpack_code
                }


        for variable in variables:
            if variable.isNestedParameterVariable():
                result += unPackNestedParameterVariables(
                    variables = variable.getTopLevelVariables(),
                    recursion = recursion + 1
                )


        return result

    parameter_parsing_code += unPackNestedParameterVariables(
        variables = top_level_parameters,
        recursion = 1
    )

    for defaulted_variable in parameters.getDefaultParameterVariables():
        default_par_code_name = _getDefaultParameterCodeName( defaulted_variable )

        function_context_decl.append( "PyObject *%s;" % default_par_code_name )
        function_context_copy.append(
            "_python_context->%s = %s;" % (
                default_par_code_name,
                default_par_code_name
            )
        )
        function_context_free.append(
            "Py_DECREF( _python_context->%s );" % default_par_code_name
        )

    parameter_parsing_codes = parameter_parsing_code.split( "\n" )

    return (
        function_parameter_variables,
        function_context_decl,
        function_context_copy,
        function_context_free,
        parameter_parsing_codes,
        parameter_release_codes
    )

def _getDecoratorsCallCode( decorators ):
    def _getCall( count ):
        return getFunctionCallCode(
            function_identifier  = Identifier( "decorator_%d" % count, 0 ),
            argument_tuple       = getSequenceCreationCode(
                sequence_kind       = "tuple",
                element_identifiers = [ Identifier( "result", 1 ) ],
            ),
            argument_dictionary  = Identifier( "NULL", 0 ),
            star_dict_identifier = None,
            star_list_identifier = None
        )

    decorator_calls = [
        "result = %s;" % _getCall( count + 1 ).getCode()
        for count in
        range( len( decorators ) )
    ]

    return decorator_calls


def _getGeneratorFunctionCode( context, function_name, function_identifier, parameters, closure_variables, user_variables, decorators, function_codes, function_filename, function_doc ):
    function_parameter_variables, function_context_decl, function_context_copy, function_context_free, parameter_parsing_codes, parameter_release_codes = _getParameterParsingCode(
        context                = context,
        function_name          = function_name,
        parameters             = parameters,
    )

    if function_parameter_variables:
        parameter_object_decl = ", " + ", ".join(
            [
                "PyObject *_python_par_" + variable.getName()
                for variable in
                function_parameter_variables
            ]
        )

        parameter_object_list = ", " + ", ".join(
            [
                "_python_par_" + variable.getName()
                for variable in
                function_parameter_variables
            ]
        )
    else:
        parameter_object_decl = ""
        parameter_object_list = ""

    function_parameter_decl = []
    parameter_context_assign = []
    function_var_inits = []

    for variable in function_parameter_variables:
        function_parameter_decl.append(
            _getLocalVariableInitCode(
                context    = context,
                variable   = variable,
                in_context = True
            )
        )
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

    for closure_variable in closure_variables:
        function_context_decl.append(
            _getLocalVariableInitCode(
                context    = context,
                variable   = closure_variable,
                in_context = True,
                shared     = True
            )
        )
        function_context_copy.append(
            "_python_context->python_closure_%s.shareWith( python_closure_%s );" % (
                closure_variable.getName(),
                closure_variable.getName()
            )
        )

    function_creation_args = _getFunctionCreationArgs(
        decorators        = decorators,
        parameters        = parameters,
        closure_variables = closure_variables,
        is_generator      = False
    )

    function_decorator_calls = _getDecoratorsCallCode(
        decorators = decorators
    )

    function_doc = getConstantHandle( context = context, constant = function_doc ).getCode()

    result = CodeTemplates.genfunc_context_body_template % {
        "function_identifier"            : function_identifier,
        "function_common_context_decl"   : _indented( function_context_decl ),
        "function_instance_context_decl" : _indented( function_parameter_decl + local_var_decl ),
        "function_context_free"          : _indented( function_context_free, 2 ),
    }

    if closure_variables or user_variables or function_parameter_variables:
        context_access_template = CodeTemplates.generator_context_access_template2  % {
            "function_identifier" : function_identifier
        }
    else:
        context_access_template = CodeTemplates.generator_context_unused_template

    result += CodeTemplates.genfunc_yielder_template % {
        "function_name"       : function_name,
        "function_identifier" : function_identifier,
        "function_body"       : _indented( function_codes, 2 ),
        "function_var_inits"  : _indented( function_var_inits, 2 ),
        "context_access"      : _indented( context_access_template, 2 ),
        "module_identifier"   : getModuleAccessCode( context = context ),
        "name_identifier"     : getConstantCode(
            context  = context,
            constant = function_name
        ),
        "filename_identifier" : getConstantCode(
            context  = context,
            constant = function_filename
        )
    }

    if parameters.getDefaultParameterCount():
        context_access_arg_parsing = CodeTemplates.generator_context_access_template % {
            "function_identifier" : function_identifier
        }
    else:
        context_access_arg_parsing = CodeTemplates.generator_context_unused_template

    result += CodeTemplates.genfunc_function_template % {
        "function_name"              : function_name,
        "function_name_obj"          : getConstantCode(
            constant = function_name,
            context  = context,
        ),
        "function_identifier"        : function_identifier,
        "parameter_parsing_code"     : _indented( parameter_parsing_codes ),
        "context_access_arg_parsing" : _indented( context_access_arg_parsing ),
        "parameter_release_code"     : _indented( parameter_release_codes ),
        "parameter_context_assign"   : _indented( parameter_context_assign, 2 ),
        "parameter_object_decl"      : parameter_object_decl,
        "parameter_object_list"      : parameter_object_list,
        "function_context_copy"      : _indented( function_context_copy ),
        "module"                     : getModuleAccessCode( context = context ),
    }

    result += CodeTemplates.make_genfunc_with_context_template % {
        "function_name"              : function_name,
        "function_name_obj"          : getConstantCode(
            context  = context,
            constant = function_name
        ),
        "function_identifier"        : function_identifier,
        "function_creation_args"     : function_creation_args,
        "function_decorator_calls"   : _indented( function_decorator_calls ),
        "function_context_copy"      : _indented( function_context_copy ),
        "function_doc"               : function_doc,
        "module"                     : getModuleAccessCode( context = context ),
    }

    return result

def _getFunctionCode( context, function_name, function_identifier, parameters, closure_variables, user_variables, decorators, function_codes, function_filename, function_doc ):
    function_parameter_variables, function_context_decl, function_context_copy, function_context_free, parameter_parsing_codes, parameter_release_codes = _getParameterParsingCode(
        context                = context,
        function_name          = function_name,
        parameters             = parameters,
    )

    function_parameter_decl = [
        _getLocalVariableInitCode(
            context    = context,
            variable   = variable,
            in_context = False,
            init_from  = "_python_par_" + variable.getName()
        )
        for variable in
        function_parameter_variables
    ]

    if function_parameter_variables:
        parameter_object_decl = ", " + ", ".join(
            [
                "PyObject *_python_par_" + variable.getName()
                for variable in
                function_parameter_variables
            ]
        )
        parameter_object_list = ", " + ", ".join(
            [ "_python_par_" + variable.getName()
              for variable in
              function_parameter_variables
            ]
        )
    else:
        parameter_object_decl = ""
        parameter_object_list = ""


    for closure_variable in closure_variables:
        function_context_decl.append(
            "PyObjectSharedLocalVariable python_closure_%s;" % closure_variable.getName()
        )
        function_context_copy.append(
            "_python_context->python_closure_%s.shareWith( python_closure_%s );" % (
                closure_variable.getName(),
                closure_variable.getName()
            )
        )

    function_creation_args = _getFunctionCreationArgs(
        decorators        = decorators,
        parameters        = parameters,
        closure_variables = closure_variables,
        is_generator      = False
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

    function_decorator_calls = _getDecoratorsCallCode(
        decorators = decorators
    )

    function_doc = getConstantCode(
        context = context,
        constant = function_doc
    )

    if context.hasLocalsDict():
        function_locals = CodeTemplates.function_dict_setup.split("\n") + function_parameter_decl + local_var_inits
    else:
        function_locals = function_parameter_decl + local_var_inits


    result = ""

    if function_context_decl:
        result += CodeTemplates.function_context_body_template % {
            "function_identifier"   : function_identifier,
            "function_context_decl" : _indented( function_context_decl ),
            "function_context_free" : _indented( function_context_free ),
        }

    if parameters.getDefaultParameterCount():
        context_access_arg_parsing = CodeTemplates.function_context_access_template % {
            "function_identifier" : function_identifier,
        }
    else:
        context_access_arg_parsing = CodeTemplates.function_context_unused_template

    if closure_variables:
        context_access_function_impl = CodeTemplates.function_context_access_template % {
            "function_identifier" : function_identifier,
        }
    else:
        context_access_function_impl = CodeTemplates.function_context_unused_template


    module_identifier = getModuleAccessCode( context = context )

    result += CodeTemplates.function_body_template % {
        "function_name"                : function_name,
        "function_identifier"          : function_identifier,
        "context_access_arg_parsing"   : context_access_arg_parsing,
        "context_access_function_impl" : context_access_function_impl,
        "parameter_parsing_code"       : _indented( parameter_parsing_codes ),
        "parameter_release_code"       : _indented( parameter_release_codes ),
        "parameter_object_decl"        : parameter_object_decl,
        "parameter_object_list"        : parameter_object_list,
        "function_locals"              : _indented( function_locals, 2 ),
        "function_body"                : _indented( function_codes, 2 ),
        "module_identifier"            : module_identifier,
        "name_identifier"              : getConstantCode(
            context  = context,
            constant = function_name
        ),
        "filename_identifier"     : getConstantCode(
            context  = context,
            constant = function_filename
        ),
    }

    if function_context_decl:
        result += CodeTemplates.make_function_with_context_template % {
            "function_name"              : function_name,
            "function_name_obj"          : getConstantCode(
                context = context,
                constant = function_name
            ),
            "function_identifier"        : function_identifier,
            "function_creation_args"     : function_creation_args,
            "function_decorator_calls"   : _indented( function_decorator_calls ),
            "function_context_copy"      : _indented( function_context_copy ),
            "function_doc"               : function_doc,
            "module"                     : getModuleAccessCode( context = context ),
        }
    else:
        result += CodeTemplates.make_function_without_context_template % {
            "function_name"              : function_name,
            "function_name_obj"          : getConstantCode(
                context  = context,
                constant = function_name
            ),
            "function_identifier"        : function_identifier,
            "function_creation_args"     : function_creation_args,
            "function_decorator_calls"   : _indented( function_decorator_calls ),
            "function_doc"               : function_doc,
            "module"                     : getModuleAccessCode( context = context ),
        }

    return result

def getGeneratorExpressionCode( context, generator, generator_identifier, generator_code, generator_conditions, generator_iterateds, loop_var_codes ):
    function_name     = "<" + generator.getFullName() + ">"
    function_filename = generator.getParentModule().getFilename()

    function_context_decl = []
    function_context_copy = []
    function_context_release = []

    function_creation_args = [ "PyObject *iterated" ]

    for closure_variable in generator.getClosureVariables():
        function_context_decl.append(
            "PyObjectSharedLocalVariable python_closure_%s;" % closure_variable.getName()
        )
        function_context_copy.append(
            "_python_context->python_closure_%s.shareWith( python_closure_%s );" % (
                closure_variable.getName(),
                closure_variable.getName()
            )
        )

        function_creation_args.append(
            "PyObjectSharedLocalVariable &python_closure_%s" % closure_variable.getName()
        )

    # Into the context the provided variables must go:
    for variable in generator.getProvidedVariables():
        assert not variable.isClosureReference()

        function_context_decl.append(
            "PyObjectLocalVariable python_var_%s;" % variable.getName()
        )

    result = ""

    result += CodeTemplates.genexpr_context_body_template % {
        "function_identifier"      : generator_identifier,
        "function_context_decl"    : _indented( function_context_decl ),
        "function_context_release" : _indented( function_context_release ),
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


    line_number_code = getCurrentLineCode( generator.getSourceReference() ) if Options.shallHaveStatementLines() else ""

    result += CodeTemplates.genexpr_function_template % {
        "function_name"              : function_name,
        "function_identifier"        : generator_identifier,
        "function_context_decl"      : _indented( function_context_decl ),
        "function_context_copy"      : _indented( function_context_copy ),
        "function_context_release"   : _indented( function_context_release ),
        "iterator_count"             : len( generator.getTargets() ),
        "iterator_making"            : _indented( iterator_making.split( "\n" ), 5 ),
        "iterator_value_assign"      : _indented( iterator_value_assign, 5 ),
        "function_body"              : getReturnCode( identifier = generator_code ),
        "module"                     : getModuleAccessCode( context = context ),
        "name_identifier"            : getConstantCode(
            context  = context,
            constant = function_name
        ),
        "filename_identifier"        : getConstantCode(
            context  = context,
            constant = function_filename
        ),
        "line_number_code"           : line_number_code,
    }

    full_name = generator.getFullName()

    result += CodeTemplates.make_genexpr_with_context_template % {
        "function_name"              : full_name,
        "function_name_obj"          : getConstantCode(
            context  = context,
            constant = full_name
        ),
        "function_identifier"        : generator_identifier,
        "function_creation_args"     : ", ".join( function_creation_args ),
        "function_context_copy"      : _indented( function_context_copy ),
        "function_doc"               : "Py_None",
        "iterator_count"             : len( generator.getTargets() ),
        "module"                     : getModuleAccessCode( context = context ),
    }

    return result


def getFunctionDecl( function ):
    return _getFunctionDecl(
        function_identifier = function.getCodeName(),
        decorators          = function.getDecorators(),
        parameters          = function.getParameters(),
        closure_variables   = function.getClosureVariables(),
        is_generator        = False
    )


def getFunctionCode( context, function, function_codes ):
    if not function.isGenerator():
        return _getFunctionCode(
            context              = context,
            function_name        = function.getFunctionName(),
            function_identifier  = function.getCodeName(),
            parameters           = function.getParameters(),
            closure_variables    = function.getClosureVariables(),
            user_variables       = function.getBody().getUserLocalVariables(),
            decorators           = function.getDecorators(),
            function_filename    = function.getParentModule().getFilename(),
            function_codes       = function_codes,
            function_doc         = function.getBody().getDoc()
        )
    else:
        return _getGeneratorFunctionCode(
            context              = context,
            function_name        = function.getFunctionName(),
            function_identifier  = function.getCodeName(),
            parameters           = function.getParameters(),
            closure_variables    = function.getClosureVariables(),
            user_variables       = function.getBody().getUserLocalVariables(),
            decorators           = function.getDecorators(),
            function_filename    = function.getParentModule().getFilename(),
            function_codes       = function_codes,
            function_doc         = function.getBody().getDoc()
        )


def getLambdaDecl( lambda_def ):
    return _getFunctionDecl(
        function_identifier = lambda_def.getCodeName(),
        parameters          = lambda_def.getParameters(),
        closure_variables   = lambda_def.getClosureVariables(),
        decorators          = (),
        is_generator        = False
    )

def getLambdaCode( context, lambda_def, lambda_codes ):
    if not lambda_def.isGenerator():
        return _getFunctionCode(
            context              = context,
            function_name        = "<lambda>",
            function_identifier  = lambda_def.getCodeName(),
            parameters           = lambda_def.getParameters(),
            user_variables       = lambda_def.getBody().getUserLocalVariables(),
            decorators           = (), # Lambda expressions can't be decorated.
            closure_variables    = lambda_def.getClosureVariables(),
            function_codes       = lambda_codes,
            function_filename    = lambda_def.getParentModule().getFilename(),
            function_doc         = None # Lambda expressions don't have doc strings
        )
    else:
        return _getGeneratorFunctionCode(
            context              = context,
            function_name        = "<lambda>",
            function_identifier  = lambda_def.getCodeName(),
            parameters           = lambda_def.getParameters(),
            user_variables       = lambda_def.getBody().getUserLocalVariables(),
            decorators           = (), # Lambda expressions can't be decorated.
            closure_variables    = lambda_def.getClosureVariables(),
            function_codes       = lambda_codes,
            function_filename    = lambda_def.getParentModule().getFilename(),
            function_doc         = None # Lambda expressions don't have doc strings
        )


def getCurrentLineCode( source_ref ):
    return "_current_line = %d;\n" % source_ref.getLineNumber()

def getCurrentExceptionObjectCode():
    return Identifier( "_exception.getObject()", 0 )

def getTupleUnpackIteratorCode( recursion ):
    return TempVariableIdentifier( "tuple_iterator_%d" % recursion )

def getTupleUnpackLeftValueCode( recursion, count ):
    return TempVariableIdentifier( "tuple_lvalue_%d_%d" % ( recursion, count ) )

def _getClosureVariableDecl( variable ):
    owner = variable.getOwner()

    if not owner.isParentVariableProvider():
        owner = owner.getParentVariableProvider()

    if variable.getReferenced().isShared():
        kind = "PyObjectSharedLocalVariable"
    else:
        kind = "PyObjectLocalVariable"

    return "%s &_python_closure_%s" % ( kind, variable.getName() )

def getClassCreationCode( code_name, dict_identifier, bases_identifier, decorators ):
    args = decorators + [ bases_identifier, dict_identifier ]

    return Identifier(
        "MAKE_CLASS_%s( %s )" % (
            code_name,
            ", ".join( getCodeTemporaryRefs( args ) )
        ),
        1
    )

def getClassDictCreationCode( context, class_def ):
    args = getClosureVariableProvisionCode(
        context           = context,
        closure_variables = class_def.getClosureVariables()
    )

    return Identifier(
        "%s( %s )" % (
            class_def.getCodeName(),
            ", ".join( args )
        ),
        1
    )

def _getClassCreationArgs( class_def ):
    class_creation_args = [
        "PyObject *decorator_%d" % ( d + 1 )
        for d in
        range( len( class_def.getDecorators() ) )
    ]
    class_creation_args.append( "PyObject *bases" )
    class_creation_args.append( "PyObject *dict" )

    class_dict_args = []

    for closure_variable in class_def.getClosureVariables():
        class_dict_args.append(
            _getClosureVariableDecl(
                variable     = closure_variable
            )
        )

    return class_creation_args, class_dict_args

def getClassDecl( class_def ):
    class_creation_args, class_dict_args = _getClassCreationArgs(
        class_def = class_def
    )

    return CodeTemplates.class_decl_template % {
        "class_identifier"    : class_def.getCodeName(),
        "class_dict_args"     : ", ".join( class_dict_args ),
        "class_creation_args" : ", ".join( class_creation_args )
    }

def getClassCode( context, class_def, class_codes ):
    class_variables = class_def.getClassVariables()

    class_var_decl = []

    for class_variable in class_variables:
        if class_variable.getName() == "__module__":
            init_from = getConstantCode(
                constant   = class_def.getParentModule().getName(),
                context    = context,
            )
        elif class_variable.getName() == "__doc__":
            init_from = getConstantCode(
                constant = class_def.getBody().getDoc(),
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
                mangle_name   = class_def.getClassName()
            )
        )

    class_creation_args, class_dict_args = _getClassCreationArgs(
        class_def = class_def
    )

    auto_static = ( "__new__", )

    if context.hasLocalsDict():
        class_locals = CodeTemplates.function_dict_setup.split("\n") + class_var_decl
    else:
        class_locals = class_var_decl

    class_dict_creation = ""

    for class_variable in class_variables:
        class_key = class_variable.getName()

        if class_key in auto_static:
            var_identifier = LocalVariableIdentifier( class_variable.getName() )
            class_dict_creation += '%s = MAKE_STATIC_METHOD( %s );\n' % (
                var_identifier.getCode(),
                var_identifier.getCodeObject()
            )


    class_body = class_def.getBody()

    local_list = _getLocalVariableList(
        context  = context,
        provider = class_body
    )


    class_dict_creation += getReturnCode(
        identifier = getLoadLocalsCode(
            provider = class_body,
            context  = context,
            mode     = "updated"
        )
    )

    class_decorator_calls = _getDecoratorsCallCode(
        decorators = class_def.getDecorators()
    )

    metaclass_variable = class_def.getParentModule().getVariableForReference(
        variable_name = "__metaclass__"
    )

    assert metaclass_variable.isModuleVariable()

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

    return CodeTemplates.class_dict_template % {
        "class_identifier"      : class_def.getCodeName(),
        "class_name"            : getConstantCode(
            constant = class_def.getClassName(),
            context  = context
        ),
        "module_name"           : getConstantCode(
            constant = context.getModuleName(),
            context = context
        ),
        "class_dict_args"       : ", ".join( class_dict_args ),
        "class_creation_args"   : ", ".join( class_creation_args ),
        "class_var_decl"        : _indented( class_locals ),
        "class_dict_creation"   : _indented( class_dict_creation, 2 ),
        "class_decorator_calls" : _indented( class_decorator_calls ),
        "class_body"            : _indented( class_codes, 2 ),
        "module_identifier"     : getModuleAccessCode( context = context ),
        "name_identifier"       : getConstantCode(
            context  = context,
            constant = class_def.getClassName()
        ),
        "filename_identifier"   : getConstantCode(
            context  = context,
            constant = class_def.getParentModule().getFilename()
        ),
        "metaclass_global_test" : getVariableTestCode(
            context  = context,
            variable = metaclass_variable
        ),
        "metaclass_global_var"  : meta_class_identifier.getCodeTemporaryRef()
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
            declaration = "extern PyObject *%s;" % constant_identifier
        else:
            declaration = "PyObject *%s;" % constant_identifier

        statements.append( declaration )

    return "\n".join( statements )

def _getConstantsDefinitionCode( context ):
    statements = []

    for constant_desc, constant_identifier in context.getConstants():
        constant_type, constant_value = constant_desc
        constant_value = constant_value.getConstant()

        # Use shortest code for ints, except when they are big, then fall fallback to
        # pickling.
        if constant_type == int and abs( constant_value ) < 2**31:
            statements.append(
                "%s = PyInt_FromLong( %s );" % (
                    constant_identifier,
                    constant_value
                )
            )

            continue

        # Note: The "str" should not be necessary, but I had an apparent g++ bug that
        # prevented it from working correctly, where UNSTREAM_STRING would return NULL
        # even when it asserts against that.
        if constant_type in ( str, tuple, list, bool, float, complex, unicode, int, long, dict, frozenset, set ):
            # Note: The marshal module cannot persist all unicode strings and
            # therefore cannot be used.  The cPickle fails to gives reproducible
            # results for some tuples, which needs clarification. In the mean time we
            # are using pickle.
            try:
                saved = pickle.dumps(
                    constant_value,
                    protocol = 0 if constant_type is unicode else 0
                )
            except TypeError:
                warning( "Problem with persisting constant '%r'." % constant_value )
                raise

            # Check that the constant is restored correctly.
            restored = cpickle.loads( saved )

            assert Contexts.compareConstants( restored, constant_value )

            if str is unicode:
                saved = saved.decode( "utf_8" )

            statements.append( "%s = UNSTREAM_CONSTANT( %s, %d );" % (
                constant_identifier,
                CppRawStrings.encodeString( saved ),
                len( saved ) )
            )
        elif constant_type is str:
            statements.append(
                "%s = UNSTREAM_STRING( %s, %d );" % (
                    constant_identifier,
                    CppRawStrings.encodeString( constant_value ),
                    len(constant_value)
                )
            )
        elif constant_value is None:
            pass
        else:
            assert False, (type(constant_value), constant_value, constant_identifier)

    return "\n        ".join( statements )


def getConstantsDeclarationCode( context ):
    constants_declarations = CodeTemplates.template_constants_declaration % {
        "constant_declarations" : _getConstantsDeclarationCode(
            context    = context,
            for_header = True
        )
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
