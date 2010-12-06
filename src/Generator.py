#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
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

from Identifiers import Identifier, ModuleVariableIdentifier, LocalVariableIdentifier, TempVariableIdentifier

import PythonOperators
import CodeTemplates
import Variables
import Options

def _indentedCode( codes, count ):
    return "\n".join( " " * count + line if line else "" for line in codes )


class PythonGeneratorBase:
    def getConstantHandle( self, context, constant ):
        return context.getConstantHandle( constant )

    def getConstantCode( self, context, constant ):
        return self.getConstantHandle( context = context, constant = constant ).getCode()

    def getConstantAccess( self, context, constant ):
        if type( constant ) is dict:
            return Identifier( "PyDict_Copy( %s )" % self.getConstantCode( constant = constant, context = context ), 1 )
        elif type( constant ) is set:
            return Identifier( "PySet_New( %s )" % self.getConstantCode( constant = constant, context = context ), 1 )
        elif type( constant ) is list:
            return Identifier( "LIST_COPY( %s )" % self.getConstantCode( constant = constant, context = context ), 1 )
        else:
            return self.getConstantHandle( context = context, constant = constant )

    def getReturnCode( self, context, identifier ):
        if identifier is not None:
            return "return %s;" % identifier.getCodeExportRef()
        else:
            return "return;"

    def getYieldCode( self, context, identifier ):
        return Identifier( "YIELD_VALUE( generator, %s )" % identifier.getCodeExportRef(), 0 )

    def getYieldTerminatorCode( self ):
        return CodeTemplates.genfunc_yield_terminator;

    def getSequenceCreationCode( self, context, sequence_kind, element_identifiers ):
        assert sequence_kind in ( "tuple", "list" )

        if sequence_kind == "tuple":
            args = [ element_identifier.getCodeTemporaryRef() for element_identifier in element_identifiers ]
        else:
            args = [ element_identifier.getCodeExportRef() for element_identifier in element_identifiers ]

        assert not ( sequence_kind == "tuple" and len( args ) == 0 )

        return Identifier( "MAKE_%s( %s )" % ( sequence_kind.upper(), ", ".join( reversed( args ) ) ), 1 )

    def getDictionaryCreationCode( self, context, keys, values ):
        args = []

        for key, value in zip( keys, values ):
            args.append( value.getCodeTemporaryRef() )
            args.append( key.getCodeTemporaryRef() )


        return Identifier( "MAKE_DICT( %s )" % ( ", ".join( reversed( args ) ) ), 1 )

    def getSetCreationCode( self, context, values ):
        args = []

        for value in reversed( values ):
            args.append( value.getCodeTemporaryRef() )

        return Identifier( "MAKE_SET( %s )" % ( ", ".join( args ) ), 1 )

    def getImportModuleCode( self, context, module_name, import_name, variable ):
        return self.getAssignmentCode(
            context    = context,
            variable   = variable,
            identifier = Identifier( """IMPORT_MODULE( %s, %s )""" % ( self.getConstantCode( constant = module_name, context = context ), self.getConstantCode( constant = import_name, context = context ) ), 1 )
        )

    def getImportModulesCode( self, context, import_specs ):
        code = ""

        for import_spec in import_specs:
            code += self.getImportModuleCode(
                context     = context,
                module_name = import_spec.getFullName(),
                import_name = import_spec.getImportName(),
                variable    = import_spec.getVariable()
            )

        return code

    def getImportFromCode( self, context, module_name, imports ):
        module_imports = []
        object_names = []

        # Do we have the "from x import *" case.
        star_import = False

        for object_name, local_var in imports:
            if object_name == "*":
                assert len( imports ) == 1

                star_import = True
            else:
                object_names.append( object_name )

                object_identifier = self.getConstantHandle( context = context, constant = object_name )


                lookup_code = self.getAssignmentCode(
                    context    = context,
                    variable   = local_var,
                    identifier = Identifier( "LOOKUP_ATTRIBUTE( _module_temp, %s )" % object_identifier.getCodeTemporaryRef(), 1 )
                )

                import_code = CodeTemplates.import_item_code % {
                    "lookup_code" : lookup_code
                }

                module_imports += import_code.split("\n")

        if not star_import:
            return CodeTemplates.import_from_template % {
                "module_name"    : module_name,
                "module_imports" : _indentedCode( module_imports, 4 ),
                "import_list"    : self.getConstantCode(
                    context  = context,
                    constant = tuple( object_names )
                )
            }
        else:
            if not context.hasLocalsDict():
                return """IMPORT_MODULE_STAR( %s, true, %s );""" % ( self.getModuleAccessCode( context = context ), self.getConstantCode( constant = module_name, context = context ) )
            else:
                return """IMPORT_MODULE_STAR( locals_dict.asObject(), false, %s );""" % self.getConstantCode( constant = module_name, context = context )

    def getMaxIndexCode( self, context ):
        return Identifier( "PY_SSIZE_T_MAX", 0 )

    def getMinIndexCode( self, context ):
        return Identifier( "0", 0 )

    def getIndexCode( self, context, identifier ):
        return Identifier( "CONVERT_TO_INDEX( %s )" % identifier.getCodeTemporaryRef(), 0 )

    def getFunctionCallCode( self, context, function_identifier, argument_tuple, argument_dictionary, star_list_identifier, star_dict_identifier ):
        if False and star_dict_identifier is not None and argument_dictionary.getCode() == "_python_dict_empty":
            # TODO: Should check for Dict and probably make a copy from the potential mapping it is
            argument_dictionary  = star_dict_identifier
            star_dict_identifier = None

        if star_dict_identifier is None:
            if star_list_identifier is None:
                return Identifier( "CALL_FUNCTION( %(named_args)s, %(pos_args)s, %(function)s )" % {
                    "function"   : function_identifier.getCodeTemporaryRef(),
                    "pos_args"   : argument_tuple.getCodeTemporaryRef(),
                    "named_args" : argument_dictionary.getCodeTemporaryRef() if argument_dictionary.getCode() != "_python_dict_empty" else "NULL"
                }, 1 )
            else:
                return Identifier( "CALL_FUNCTION_STAR_LIST( %(star_list_arg)s, %(named_args)s, %(pos_args)s, %(function)s )" % {
                    "function"   : function_identifier.getCodeTemporaryRef(),
                    "pos_args"   : argument_tuple.getCodeTemporaryRef(),
                    "named_args" : argument_dictionary.getCodeTemporaryRef() if argument_dictionary.getCode() != "_python_dict_empty" else "NULL",
                    "star_list_arg" : star_list_identifier.getCodeTemporaryRef()
                }, 1 )
        else:
            if star_list_identifier is not None:
                return Identifier( "CALL_FUNCTION_STAR_BOTH( %(star_dict_arg)s, %(star_list_arg)s, %(named_args)s, %(pos_args)s, %(function)s )" % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "pos_args"      : argument_tuple.getCodeTemporaryRef(),
                    "named_args"    : argument_dictionary.getCodeTemporaryRef(),
                    "star_list_arg" : star_list_identifier.getCodeTemporaryRef(),
                    "star_dict_arg" : star_dict_identifier.getCodeTemporaryRef()
                }, 1 )
            else:
                return Identifier( "CALL_FUNCTION_STAR_DICT( %(star_dict_arg)s, %(named_args)s, %(pos_args)s, %(function)s )" % {
                    "function"      : function_identifier.getCodeTemporaryRef(),
                    "pos_args"      : argument_tuple.getCodeTemporaryRef(),
                    "named_args"    : argument_dictionary.getCodeTemporaryRef(),
                    "star_dict_arg" : star_dict_identifier.getCodeTemporaryRef()
                }, 1 )


    def getIteratorCreationCode( self, context, iterated ):
        return Identifier( "MAKE_ITERATOR( %s )" % ( iterated.getCodeTemporaryRef() ), 1 )

    def getIteratorNextCode( self, context, iterator ):
        return Identifier( "ITERATOR_NEXT( %s )" % ( iterator.getCodeTemporaryRef() ), 1 )

    def getUnpackNextCode( self, context, iterator, element_count ):
        return Identifier( "UNPACK_NEXT( %s, %d )" % ( iterator.getCodeTemporaryRef(), element_count-1 ), 1 )

    def getUnpackTupleCode( self, context, assign_source, iterator_identifier, lvalue_identifiers ):
        result = "PyObjectTemporary %s( %s );\n" % ( iterator_identifier.getCode(), self.getIteratorCreationCode( context = context, iterated = assign_source ).getCodeExportRef() )

        for count, lvalue_identifier in enumerate( lvalue_identifiers ):
            result += "PyObjectTemporary %s( %s );\n" % ( lvalue_identifier.getCode(), self.getUnpackNextCode( context = context, iterator = iterator_identifier, element_count = count+1 ).getCodeExportRef( ) )

        result += "UNPACK_ITERATOR_CHECK( %s );\n" % iterator_identifier.getCodeTemporaryRef()

        return result

    def getAttributeLookupCode( self, context, attribute_name, source ):
        attribute = self.getConstantCode( context = context, constant = attribute_name )

        return Identifier( "LOOKUP_ATTRIBUTE( %s, %s )" % ( source.getCodeTemporaryRef(), attribute ), 1 )

    def getSubscriptLookupCode( self, context, subscript, source ):
        return Identifier( "LOOKUP_SUBSCRIPT( %s, %s )" % ( source.getCodeTemporaryRef(), subscript.getCodeTemporaryRef() ), 1 )

    def getHasKeyCode( self, context, source, key ):
        return Identifier( "HAS_KEY( %s, %s )" % ( source.getCodeTemporaryRef(), key.getCodeTemporaryRef() ), 0 )

    def getSliceLookupCode( self, context, lower, upper, source ):
        return Identifier( "LOOKUP_SLICE( %s, %s, %s )" % ( source.getCodeTemporaryRef(), lower.getCodeTemporaryRef(), upper.getCodeTemporaryRef() ), 1 )

    def getSliceObjectCode( self, context, lower, upper, step ):
        lower = "Py_None" if lower is None else lower.getCodeTemporaryRef()
        upper = "Py_None" if upper is None else upper.getCodeTemporaryRef()
        step  = "Py_None" if step  is None else step.getCodeTemporaryRef()

        return Identifier( "MAKE_SLICEOBJ( %s, %s, %s )" % ( lower, upper, step ), 1 )

    def getStatementCode( self, identifier ):
        return identifier.getCodeDropRef() + ";"

    def getOperationCode( self, context, operator, identifiers ):
        identifier_refs = [ identifier.getCodeTemporaryRef() for identifier in identifiers ]

        if operator == "PyNumber_Power":
            assert len( identifiers ) == 2

            return Identifier( "POWER_OPERATION( %s, %s )" % ( identifier_refs[0], identifier_refs[1] ), 1 )
        elif len( identifiers ) == 2:
            return Identifier( "BINARY_OPERATION( %s, %s, %s )" % ( operator, identifier_refs[0], identifier_refs[1] ), 1 )
        elif len( identifiers ) == 1:
            return Identifier( "UNARY_OPERATION( %s, %s )" % ( operator, identifier_refs[0] ), 1 )
        else:
            assert False, (operator, identifiers)

    def getPrintCode( self, context, newline, identifiers, target_file ):
        args = [ "true" if newline else "false", target_file.getCodeTemporaryRef() if target_file is not None else "NULL" ]

        args += [ identifier.getCodeTemporaryRef() for identifier in identifiers ]

        return "PRINT_ITEMS( %s );" % ( ", ".join( args ) )

    def getContractionCallCode( self, context, contraction, contraction_identifier, contraction_iterated ):
        args = [ contraction_iterated.getCodeTemporaryRef() ]

        for variable in contraction.getClosureVariables():
            if variable.isClosureReference():
                args.append( self.getVariableHandle( context = context, variable = variable.getReferenced() ).getCode() )

        if not contraction.isExpressionGenerator():
            prefix = ""
        else:
            prefix = "MAKE_FUNCTION_"

        return Identifier( "%s%s( %s )" % ( prefix, contraction_identifier, ", ".join( args ) ), 1 )

    def getLambdaExpressionReferenceCode( self, context, lambda_expression, default_values ):
        return self.getFunctionCreationCode(
            function       = lambda_expression,
            default_values = default_values,
            decorators     = (),
            context        = context
        )

    def getConditionalExpressionCode( self, context, condition, codes_no, codes_yes ):
        if codes_yes.getCheapRefCount() == codes_no.getCheapRefCount():
            if codes_yes.getCheapRefCount == 0:
                return Identifier( "( %s ? %s : %s )" % ( condition.getCode(), codes_yes.getCodeTemporaryRef(), codes_no.getCodeTemporaryRef() ), 0 )
            else:
                return Identifier( "( %s ? %s : %s )" % ( condition.getCode(), codes_yes.getCodeExportRef(), codes_no.getCodeExportRef() ), 1 )
        else:
            return Identifier( "( %s ? %s : %s )" % ( condition.getCode(), codes_yes.getCodeExportRef(), codes_no.getCodeExportRef() ), 1 )

    def getGeneratorExpressionCreationCode( self, context, iterated_identifier, generator_expression ):
        args =  [ self.getIteratorCreationCode( context = context, iterated = iterated_identifier ).getCodeExportRef() ]

        args += [ self.getVariableHandle( variable = closure_variable.getReferenced(), context = context ).getCode() for closure_variable in generator_expression.getClosureVariables() if closure_variable.isClosureReference() ]


        return Identifier(
            "MAKE_FUNCTION_%s( %s )" % (
                generator_expression.identifier,
                ", ".join( args )
            ),
            1
        )

    def getFunctionCreationCode( self, context, function, decorators, default_values ):
        args = [ identifier.getCodeTemporaryRef() for identifier in decorators ]

        args += [ identifier.getCodeExportRef() for identifier in default_values ]

        for variable in function.getClosureVariables():
            assert variable.isClosureReference()

            if not function.getParentVariableProvider().isClassReference():
                variable = variable.getReferenced()

            args.append( self.getVariableHandle( context = context, variable = variable ).getCode() )


        return Identifier(
            "MAKE_FUNCTION_%s( %s )" % (
                function.getCodeName(),
                ", ".join( args )
            ),
            1
        )

    def getBranchCode( self, context, conditions, branches_codes ):
        keyword = "if"

        result = ""

        for condition, branch_codes in zip( conditions, branches_codes ):
            if condition is not None:
                result += """\
%s ( %s )
{
%s
}
""" % ( keyword, condition.getCode(), _indentedCode( branch_codes, 4 ) )

                keyword = "else if"


        if len( conditions ) == len( branches_codes ) - 1 and branches_codes[-1]:
            result += """\
else
{
%s
}""" % ( _indentedCode( branches_codes[-1], 4 ) )

        result = result.rstrip()

        return result

    def getLoopContinueCode( self, needs_exceptions ):
        if needs_exceptions:
            return "throw ContinueException();"
        else:
            return "continue;"

    def getLoopBreakCode( self, needs_exceptions ):
        if needs_exceptions:
            return "throw BreakException();"
        else:
            return "break;"

    def getComparisonExpressionCode( self, context, comparators, operands ):
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

                comparison = Identifier( "%s( %s, %s )" % ( py_api, left.getCodeTemporaryRef(), right.getCodeTemporaryRef() ), reference )
            elif comparator in PythonOperators.rich_comparison_operators:
                comparison = Identifier( "RICH_COMPARE( %s, %s, %s )" % ( PythonOperators.rich_comparison_operators[ comparator ], right.getCodeTemporaryRef(), left.getCodeTemporaryRef() ), 1 )
            elif comparator == "Is":
                comparison = Identifier( "BOOL_FROM( %s == %s )" % ( left.getCodeTemporaryRef(), right.getCodeTemporaryRef() ), 0 )
            elif comparator == "IsNot":
                comparison = Identifier( "BOOL_FROM( %s != %s )" % ( left.getCodeTemporaryRef(), right.getCodeTemporaryRef() ), 0 )
            else:
                assert False, comparator

        else:
            left_tmp = operands[0]

            comparison = ""

            for count, comparator in enumerate( comparators ):
                right_tmp = operands[ count + 1 ].getCodeTemporaryRef()

                if count < len( comparators ) - 1:
                    temp_storage_var = context.getTempObjectVariable()

                    right_tmp = "(%s = %s)" % ( temp_storage_var.getCode(), right_tmp )

                if comparator in PythonOperators.normal_comparison_operators:
                    assert False, comparator
                elif comparator in PythonOperators.rich_comparison_operators:
                    chunk = "RICH_COMPARE_BOOL( %s, %s, %s )" % ( PythonOperators.rich_comparison_operators[ comparator ], right_tmp, left_tmp.getCodeTemporaryRef() )
                elif comparator == "Is":
                    chunk = "( %s == %s )" % ( left_tmp.getCodeTemporaryRef(), right_tmp )
                elif comparator == "IsNot":
                    chunk = "( %s != %s )" % ( left_tmp.getCodeTemporaryRef(), right_tmp )
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

    def getComparisonExpressionBoolCode( self, context, comparators, operands ):
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

                comparison = Identifier( "%s_BOOL( %s, %s )" % ( py_api, left.getCodeTemporaryRef(), right.getCodeTemporaryRef() ), reference )
            elif comparator in PythonOperators.rich_comparison_operators:
                comparison = Identifier( "RICH_COMPARE_BOOL( %s, %s, %s )" % ( PythonOperators.rich_comparison_operators[ comparator ], right.getCodeTemporaryRef(), left.getCodeTemporaryRef() ), 0 )
            elif comparator == "Is":
                comparison = Identifier( "(%s == %s)" % ( left.getCodeTemporaryRef(), right.getCodeTemporaryRef() ), 0 )
            elif comparator == "IsNot":
                comparison = Identifier( "( %s != %s )" % ( left.getCodeTemporaryRef(), right.getCodeTemporaryRef() ), 0 )
            else:
                assert False, comparator

        else:
            left_tmp = operands[0]

            comparison = ""

            for count, comparator in enumerate( comparators ):
                right_tmp = operands[ count + 1 ].getCodeTemporaryRef()

                if count < len( comparators ) - 1:
                    temp_storage_var = context.getTempObjectVariable()

                    right_tmp = "(%s = %s)" % ( temp_storage_var.getCode(), right_tmp )

                if comparator in PythonOperators.normal_comparison_operators:
                    assert False, comparator
                elif comparator in PythonOperators.rich_comparison_operators:
                    chunk = "RICH_COMPARE_BOOL( %s, %s, %s )" % ( PythonOperators.rich_comparison_operators[ comparator ], right_tmp, left_tmp.getCodeTemporaryRef() )
                elif comparator == "Is":
                    chunk = "( %s == %s )" % ( left_tmp.getCodeTemporaryRef(), right_tmp )
                elif comparator == "IsNot":
                    chunk = "( %s != %s )" % ( left_tmp.getCodeTemporaryRef(), right_tmp )
                else:
                    assert False, comparator

                if comparison == "":
                    comparison = chunk
                else:
                    comparison = comparison + " && " + chunk

                if count < len( comparators ):
                    left_tmp = temp_storage_var

            comparison = Identifier( "( %s )" % comparison, 0 )

        return comparison


    def getConditionNotCode( self, context, condition ):
        return Identifier( "UNARY_NOT( %s )" % condition.getCodeTemporaryRef(), 0 )

    def getConditionNotBoolCode( self, context, condition ):
        return Identifier( "(!( %s ))" % condition.getCodeTemporaryRef(), 0 )

    def getConditionCheckTrueCode( self, context, condition ):
        return Identifier( "CHECK_IF_TRUE( %s )" % condition.getCodeTemporaryRef(), 0 )

    def getConditionCheckFalseCode( self, context, condition ):
        return Identifier( "CHECK_IF_FALSE( %s )" % condition.getCodeTemporaryRef(), 0 )

    def getTrueExpressionCode( self ):
        return Identifier( "true", 0 )

    def getFalseExpressionCode( self ):
        return Identifier( "false", 0 )

    def getSelectionOrCode( self, context, conditions ):
        result = " ?: ".join( [ "SELECT_IF_TRUE( %s )" % condition.getCodeExportRef() for condition in conditions[:-1] ] )

        return Identifier( "(%s ?: %s)" % ( result, conditions[-1].getCodeExportRef() ), 1 )

    def getSelectionAndCode( self, context, conditions ):
        result = " ?: ".join( [ "SELECT_IF_FALSE( %s )" % condition.getCodeExportRef() for condition in conditions[:-1] ] )

        return Identifier( "(%s ?: %s)" % ( result, conditions[-1].getCodeExportRef() ), 1 )

    def getAttributeAssignmentCode( self, context, target, attribute_name, identifier ):
        attribute = self.getConstantCode( context = context, constant = attribute_name )

        return "SET_ATTRIBUTE( %s, %s, %s );" % ( target.getCodeTemporaryRef(), attribute, identifier.getCodeTemporaryRef() )

    def getAttributeDelCode( self, context, target, attribute_name ):
        attribute = self.getConstantCode( context = context, constant = attribute_name )

        return "DEL_ATTRIBUTE( %s, %s );" % ( target.getCodeTemporaryRef(), attribute )

    def getSliceAssignmentCode( self, context, target, lower, upper, identifier  ):
        return "SET_SLICE( %s, %s, %s, %s );" % ( target.getCodeTemporaryRef(), lower.getCodeTemporaryRef(), upper.getCodeTemporaryRef(), identifier.getCodeTemporaryRef() )

    def getSliceDelCode( self, context, target, lower, upper ):
        return "DEL_SLICE( %s, %s, %s );" % ( target.getCodeTemporaryRef(), lower.getCodeTemporaryRef() if lower is not None else "Py_None", upper.getCodeTemporaryRef() if upper is not None else "Py_None" )

    def getWithNames( self, context ):
        with_count = context.allocateWithNumber()

        return TempVariableIdentifier( "_python_with_context_%d" % with_count ), TempVariableIdentifier( "_python_with_value_%d" % with_count ),


    def getWithCode( self, context, body_codes, assign_codes, source_identifier, with_manager_identifier, with_value_identifier ):

        traceback_name = context.getTracebackName()
        traceback_filename = context.getTracebackFilename()

        return CodeTemplates.with_template % {
            "assign"            : _indentedCode( assign_codes.split("\n") if assign_codes is not None else ( """// No "as" target variable for with'ed expression""", ), 8 ),
            "body"              : _indentedCode( body_codes, 8 ),
            "source"            : source_identifier.getCodeExportRef(),
            "manager"           : with_manager_identifier.getCode(),
            "value"             : with_value_identifier.getCode(),
            "with_count"        : context.with_count,
            "module_identifier" : self.getModuleAccessCode( context = context ),
            "triple_none_tuple" : self.getConstantCode( context = context, constant = ( None, None, None ) ),
            "name_identifier"   : self.getConstantCode( context = context, constant = traceback_name ),
            "file_identifier"   : self.getConstantCode( context = context, constant = traceback_filename ),
        }

    def getForLoopNames( self, context ):
        for_count = context.allocateForLoopNumber()

        return "_python_for_loop_iterator_%d" % for_count, "_python_for_loop_itervalue_%d" % for_count, TempVariableIdentifier( "itertemp_%d" % for_count )

    def getForLoopCode( self, context, line_number_code, iterator, iter_name, iter_value, iter_object, loop_var_code, loop_body_codes, loop_else_codes, needs_exceptions ):
        return CodeTemplates.getForLoopTemplate( needs_exceptions = needs_exceptions, has_else_codes = loop_else_codes ) % {
            "body"                     : _indentedCode( loop_body_codes, 8 ),
            "else_codes"               : _indentedCode( loop_else_codes, 4 ),
            "iterator"                 : iterator.getCodeExportRef(),
            "line_number_code"         : line_number_code,
            "loop_iter_identifier"     : iter_name,
            "loop_value_identifier"    : iter_value,
            "loop_object_identifier"   : iter_object.getCode(),
            "loop_var_assignment_code" : _indentedCode( loop_var_code.split("\n"), 12 ),
            "indicator_name"           : "_python_for_loop_indicator_%d" % context.allocateForLoopNumber()
        }

    def getWhileLoopCode( self, context, condition, loop_body_codes, loop_else_codes, needs_exceptions ):
        return CodeTemplates.getWhileLoopTemplate( needs_exceptions = needs_exceptions, has_else_codes = loop_else_codes ) % {
            "condition"       : condition.getCode(),
            "loop_body_codes" : _indentedCode( loop_body_codes, 4 ),
            "loop_else_codes" : _indentedCode( loop_else_codes, 4 ),
            "indicator_name"  : "_python_for_loop_indicator_%d" % context.allocateWhileLoopNumber()
        }

    def _getGlobalVariableHandle( self, context, variable ):
        assert variable.isModuleVariable()

        var_name = variable.getName()
        context.addGlobalVariableNameUsage( var_name )

        return Identifier( "_mvar_%s_%s.asObject()" % ( context.getModuleCodeName(), var_name ), 1 )

    def getVariableHandle( self, context, variable ):
        assert isinstance( variable, Variables.Variable ), variable

        var_name = variable.getName()

        if variable.isLocalVariable() or variable.isClassVariable():
            return context.getLocalHandle( var_name = variable.getName() )
        elif variable.isClosureReference():
            return context.getClosureHandle( var_name = variable.getName() )
        elif variable.isModuleVariable():
            context.addGlobalVariableNameUsage( var_name )

            if not context.hasLocalsDict():
                return ModuleVariableIdentifier( var_name, context.getModuleCodeName() )
            else:
                return Identifier( "_mvar_%s_%s.asObject( locals_dict.asObject() )" % ( context.getModuleCodeName(), var_name ), 1 )
        else:
            assert False, variable

    def getAssignmentCode( self, context, variable, identifier ):
        assert isinstance( variable, Variables.Variable ), variable

        if variable.getOwner().isModule():
            var_name = variable.getName()

            context.addGlobalVariableNameUsage( var_name )

            return "_mvar_%s_%s.assign( %s );" % ( context.getModuleCodeName(), var_name, identifier.getCodeExportRef() )
        else:
            return "%s = %s;" % ( self.getVariableHandle( variable = variable, context = context ).getCode(), identifier.getCodeExportRef() )

    def getVariableDelCode( self, context, variable ):
        assert isinstance( variable, Variables.Variable ), variable

        if variable.isModuleVariable():
            var_name = variable.getName()

            context.addGlobalVariableNameUsage( var_name )

            return "_mvar_%s_%s.del();" % ( context.getModuleCodeName(), var_name )
        else:
            return "%s.del();" % self.getVariableHandle( variable = variable, context = context ).getCode()

    def getVariableTestCode( self, context, variable ):
        assert isinstance( variable, Variables.Variable ), variable

        if variable.isModuleVariable():
            var_name = variable.getName()

            context.addGlobalVariableNameUsage( var_name )

            return "_mvar_%s_%s.isInitialized()" % ( context.getModuleCodeName(), var_name )
        else:
            return "%s.isInitialized();" % self.getVariableHandle( variable = variable, context = context ).getCode()

    def getSequenceElementCode( self, context, sequence, index ):
        return Identifier( "SEQUENCE_ELEMENT( %s, %d )" % ( sequence.getCodeTemporaryRef(), index ), 1 )

    def getSubscriptAssignmentCode( self, context, subscribed, subscript, identifier ):
        return """SET_SUBSCRIPT( %s, %s, %s );""" % ( subscribed.getCodeTemporaryRef(), subscript.getCodeTemporaryRef(), identifier.getCodeTemporaryRef() )

    def getSubscriptDelCode( self, context, subscribed, subscript ):
        return """DEL_SUBSCRIPT( %s, %s );""" % ( subscribed.getCodeTemporaryRef(), subscript.getCodeTemporaryRef() )

    def _getInplaceOperationCode( self, operator, operand1, operand2 ):
        operator = PythonOperators.inplace_operator_opcodes[ operator ]

        if operator == "PyNumber_InPlacePower":
            return Identifier( "POWER_OPERATION_INPLACE( %s, %s )" % ( operand1.getCodeTemporaryRef(), operand2.getCodeTemporaryRef() ), 1 )
        else:
            return Identifier( "BINARY_OPERATION( %s, %s, %s )" % ( operator, operand1.getCodeTemporaryRef(), operand2.getCodeTemporaryRef() ), 1 )

    def getInplaceVarAssignmentCode( self, context, variable, operator, identifier ):
        value_identifier = Identifier( "value.asObject()", 0 )
        result_identifier = Identifier( "result", 0 )

        return CodeTemplates.template_inplace_var_assignment % {
            "assign_source_identifier" : self.getVariableHandle( variable = variable, context = context ).getCodeExportRef(),
            "inplace_operation_code" : self._getInplaceOperationCode( operator = operator, operand1 = value_identifier, operand2 = identifier ).getCode(),
            "assignment_code" : self.getAssignmentCode( variable = variable, context = context, identifier = result_identifier )
        }


    def getInplaceSubscriptAssignmentCode( self, context, subscribed, subscript, operator, identifier ):
        value_identifier = Identifier( "value.asObject()", 0 )

        return """\
{
    PyObjectTemporary subscribed( %s );
    PyObjectTemporary subscript( %s );
    PyObjectTemporary value( LOOKUP_SUBSCRIPT( subscribed.asObject(), subscript.asObject() ) );

    PyObject *result = %s;

    if ( result != value.asObject() )
    {
        SET_SUBSCRIPT( subscribed.asObject(), subscript.asObject(), result );
    }

    Py_DECREF( result );
}""" % ( subscribed.getCodeExportRef(), subscript.getCodeExportRef(), self._getInplaceOperationCode( operator = operator, operand1 = value_identifier, operand2 = identifier ).getCode() )

    def getInplaceAttributeAssignmentCode( self, context, target, attribute_name, operator, identifier ):
        attribute = self.getConstantCode( context = context, constant = attribute_name )

        value_identifier = Identifier( "value.asObject()", 0 )

        return """\
{
    PyObjectTemporary target( %s );
    PyObject *attribute = %s;
    PyObjectTemporary value( LOOKUP_ATTRIBUTE ( target.asObject(), attribute ) );

    PyObject *result = %s;

    if ( result != value.asObject() )
    {
        SET_ATTRIBUTE( target.asObject(), attribute, result );
    }

    Py_DECREF( result );
}""" % ( target.getCodeExportRef(), attribute, self._getInplaceOperationCode( operator = operator, operand1 = value_identifier, operand2 = identifier ).getCode() )

    def getInplaceSliceAssignmentCode( self, context, target, lower, upper, operator, identifier ):
        value_identifier = Identifier( "value.asObject()", 0 )

        return """\
{
    PyObjectTemporary target( %s );
    PyObjectTemporary value( LOOKUP_SLICE( target.asObject(), %s, %s ) );
    PyObjectTemporary updated( %s );

    SET_SLICE( target.asObject(), %s, %s, updated.asObject() );
}""" % ( target.getCodeExportRef(), lower.getCode(), upper.getCode(), self._getInplaceOperationCode( operator = operator, operand1 = value_identifier, operand2 = identifier ).getCode(), lower.getCode(), upper.getCode() )

    def getTryFinallyCode( self, context, code_tried, code_final ):
        return CodeTemplates.try_finally_template % {
            "try_count"  : context.allocateTryNumber(),
            "tried_code" : _indentedCode( code_tried, 4 ),
            "final_code" : _indentedCode( code_final, 4 )
        }

    def getTryExceptCode( self, context, code_tried, exception_identifiers, exception_assignments, catcher_codes, else_code ):
        exception_code = []

        cond_keyword = "if"

        for exception_identifier, exception_assignment, handler_code in zip( exception_identifiers, exception_assignments, catcher_codes ):
            if exception_identifier is not None:
                exception_code.append( "%s (_exception.matches(%s))" % ( cond_keyword, exception_identifier.getCodeTemporaryRef() ) )
            else:
                exception_code.append( "%s (true)" % cond_keyword )

            exception_code.append( "{" )
            exception_code.append( "    traceback = false;" )

            if exception_assignment is not None:
                exception_code.append( _indentedCode( exception_assignment.split("\n"), 4 ) )

            exception_code += _indentedCode( handler_code, 4 ).split("\n")
            exception_code.append( "}" )

            cond_keyword = "else if"

        exception_code += [ "else", "{", "    throw;", "}" ]

        tb_making = self.getTracebackMakingIdentifier( context, "_exception.getLine()" ).getCodeExportRef()

        if else_code is not None:
            return CodeTemplates.try_except_else_template % {
                "tried_code"     : _indentedCode( code_tried, 4 ),
                "exception_code" : _indentedCode( exception_code, 4 ),
                "else_code"      : _indentedCode( else_code, 4 ),
                "tb_making"      : tb_making,
                "except_count"   : context.allocateTryNumber()
            }
        else:
            return CodeTemplates.try_except_template % {
                "tried_code"     : _indentedCode( code_tried, 4 ),
                "exception_code" : _indentedCode( exception_code, 4 ),
                "tb_making"      : tb_making,
            }


    def getRaiseExceptionCode( self, context, exception_type_identifier, exception_value_identifier, exception_tb_identifier, exception_tb_maker ):
        if exception_value_identifier is None and exception_tb_identifier is None:
            return "traceback = true; RAISE_EXCEPTION( %s, %s );" % ( exception_type_identifier.getCodeExportRef(), exception_tb_maker.getCodeExportRef() )
        elif exception_tb_identifier is None:
            return "traceback = true; RAISE_EXCEPTION( %s, %s, %s );" % ( exception_type_identifier.getCodeExportRef(), exception_value_identifier.getCodeExportRef(), exception_tb_maker.getCodeExportRef() )
        else:
            return "traceback = true; RAISE_EXCEPTION( %s, %s, %s );" % ( exception_type_identifier.getCodeExportRef(), exception_value_identifier.getCodeExportRef(), exception_tb_identifier.getCodeExportRef() )

    def getReRaiseExceptionCode( self, context ):
        return "RERAISE_EXCEPTION();"

    def getAssertCode( self, context, condition_identifier, failure_identifier, exception_tb_maker ):
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

    def _getLocalVariableList( self, context, provider ):
        if provider.isFunctionReference():
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

        return [ "&%s" % self.getVariableHandle( variable = variable, context = context ).getCode() for variable in variables if not variable.isModuleVariable() ]


    def getLoadDirCode( self, context, provider ):
        if provider.isModule():
            return Identifier( "PyDict_Keys( %s )" % self.getLoadGlobalsCode( context = context, module = provider ).getCodeTemporaryRef(), 1 )
        else:
            if not context.hasLocalsDict():
                local_list = self._getLocalVariableList( context = context, provider = provider )

                return Identifier( "MAKE_LOCALS_DIR( %s )" % ", ".join( local_list ), 1 )
            else:
                return Identifier( "PyDict_Keys( locals.asObject() )", 1 )

    def getLoadVarsCode( self, context, identifier ):
        return Identifier( "LOOKUP_VARS( %s )" % identifier.getCodeTemporaryRef(), 1 )

    def getLoadGlobalsCode( self, context, module ):
        return Identifier( "PyModule_GetDict( %(module_identifier)s )" % { "module_identifier" : self.getModuleAccessCode( context ) }, 0 )

    def getLoadLocalsCode( self, context, provider, direct ):
        assert not provider.isModule()

        if not context.hasLocalsDict():
            local_list = [ "&%s" % self.getVariableHandle( variable = variable, context = context ).getCode() for variable in provider.getVariables() if not variable.isModuleVariable() ]

            return Identifier( "MAKE_LOCALS_DICT( %s )" % ", ".join( local_list ), 1 )
        else:
            if direct:
                return Identifier( "locals_dict.asObject()", 0 )
            else:
                return Identifier( "PyDict_Copy( locals_dict.asObject() )", 1 )

    def getStoreLocalsCode( self, context, source_identifier, provider ):
        assert not provider.isModule()

        local_list = [ "&%s" % self.getVariableHandle( variable = variable, context = context ).getCode() for variable in provider.getVariables() if not variable.isModuleVariable() ]

        code = ""

        for variable in provider.getVariables():
            if not variable.isModuleVariable():
                key_identifier = self.getConstantHandle( context = context, constant = variable.getName() )

                var_assign_code = self.getAssignmentCode(
                    context    = context,
                    variable   = variable,
                    identifier = self.getSubscriptLookupCode(
                        context   = context,
                        subscript = key_identifier,
                        source    = source_identifier
                    )
                )

                code += """\
if ( %s )
{
   %s
}
""" % ( self.getHasKeyCode( context = context, source = source_identifier, key = key_identifier ).getCode(), var_assign_code )

        return code

    def getFutureFlagsCode( self, future_division, unicode_literals, absolute_import, future_print ):
        result = []

        if future_division:
            result.append( "CO_FUTURE_DIVISION" )

        if unicode_literals:
            result.append( "CO_FUTURE_UNICODE_LITERALS" )

        if absolute_import:
            result.append( "CO_FUTURE_ABSOLUTE_IMPORT" )

        if future_print:
            result.append( "CO_FUTURE_PRINT_FUNCTION" )

        if result:
            return " | ".join( result )
        else:
            return 0


    def getEvalCode( self, context, mode, exec_code, globals_identifier, locals_identifier, future_flags, provider ):
        if provider.isModule():
            return Identifier(
                CodeTemplates.eval_global_template % {
                    "globals_identifier"     : globals_identifier.getCodeTemporaryRef(),
                    "locals_identifier"      : locals_identifier.getCodeTemporaryRef(),
                    "make_globals_identifier" : self.getLoadGlobalsCode( context = context, module = provider ).getCodeExportRef(),
                    "source_identifier"      : exec_code.getCodeTemporaryRef(),
                    "filename_identifier"    : self.getConstantCode( constant = "<string>", context = context ),
                    "mode_identifier"        : self.getConstantCode( constant = "eval", context = context ),
                    "future_flags"           : future_flags,
            }, 1 )
        else:
            make_globals_identifier = self.getLoadGlobalsCode( context = context, module = provider ).getCodeExportRef()
            make_locals_identifier = self.getLoadLocalsCode( context = context, provider = provider, direct = True ).getCodeExportRef()

            return Identifier(
                CodeTemplates.eval_local_template % {
                    "globals_identifier"      : globals_identifier.getCodeTemporaryRef(),
                    "locals_identifier"       : locals_identifier.getCodeTemporaryRef(),
                    "make_globals_identifier" : make_globals_identifier,
                    "make_locals_identifier"  : make_locals_identifier,
                    "source_identifier"       : exec_code.getCodeTemporaryRef(),
                    "filename_identifier"     : self.getConstantCode( constant = "<string>", context = context ),
                    "mode_identifier"         : self.getConstantCode( constant = "eval", context = context ),
                    "future_flags"            : future_flags,
            }, 1 )

    def getExecCode( self, context, exec_code, globals_identifier, locals_identifier, future_flags, provider ):
        if provider.isModule():
            return CodeTemplates.exec_global_template % {
                "globals_identifier"      : globals_identifier.getCodeExportRef(),
                "locals_identifier"       : locals_identifier.getCodeExportRef(),
                "make_globals_identifier" : self.getLoadGlobalsCode( context = context, module = provider ).getCodeExportRef(),
                "source_identifier"       : exec_code.getCodeTemporaryRef(),
                "filename_identifier"     : self.getConstantCode( constant = "<string>", context = context ),
                "mode_identifier"         : self.getConstantCode( constant = "exec", context = context ),
                "future_flags"            : future_flags,
            }
        else:
            locals_temp_identifier = Identifier( "locals.asObject()", 0 )

            make_globals_identifier = self.getLoadGlobalsCode( context = context, module = provider ).getCodeExportRef()
            make_locals_identifier = self.getLoadLocalsCode( context = context, provider = provider, direct = True ).getCodeExportRef()

            return CodeTemplates.exec_local_template % {
                "globals_identifier"      : globals_identifier.getCodeExportRef(),
                "locals_identifier"       : locals_identifier.getCodeExportRef(),
                "make_globals_identifier" : make_globals_identifier,
                "make_locals_identifier"  : make_locals_identifier,
                "source_identifier"       : exec_code.getCodeTemporaryRef(),
                "filename_identifier"     : self.getConstantCode( constant = "<string>", context = context ),
                # TODO: Make this optional.
                # filename_identifier"    : context.getConstantHandle( constant = provider.getParentModule().getFullName() + "::exec" ).getCode(),
                "mode_identifier"         : self.getConstantCode( constant = "exec", context = context ),
                "future_flags"            : future_flags,
                "store_locals_code"       : _indentedCode( self.getStoreLocalsCode( context = context, source_identifier = locals_temp_identifier, provider = provider ).split("\n"), 8 )
            }


    def getBuiltinOpenCode( self, context, filename, mode, buffering ):
        return Identifier( "OPEN_FILE( %s, %s, %s )" % (
            filename.getCodeTemporaryRef()  if filename  is not None else "NULL",
            mode.getCodeTemporaryRef()      if mode      is not None else "NULL",
            buffering.getCodeTemporaryRef() if buffering is not None else "NULL"
        ), 1 )

class PythonModuleGenerator( PythonGeneratorBase ):
    def __init__( self, module_name ):
        self.module_name = module_name

    def getName( self ):
        return self.module_name

    def getModuleAccessCode( self, context ):
        return Identifier( "_module_%s" % context.getModuleCodeName(), 0 ).getCode()

    def getFrameMakingIdentifier( self, context, line ):
        return Identifier( """MAKE_FRAME( %(module_identifier)s, %(module_filename_identifier)s, %(code_identifier)s, %(line)s )""" % {
            "module_identifier"          : self.getModuleAccessCode( context = context ),
            "module_filename_identifier" : self.getConstantCode( context = context, constant = context.getTracebackFilename() ),
            "code_identifier"            : self.getConstantCode( context = context, constant = context.getTracebackName() ),
            "line"                       : line
        }, 1 )

    def getTracebackMakingIdentifier( self, context, line ):
        return Identifier( "MAKE_TRACEBACK( %s, %s )" % ( self.getFrameMakingIdentifier( context = context, line = line ).getCodeTemporaryRef(), line ), 1 )

    def getModuleIdentifier( self, module_name ):
        return module_name.replace( ".", "__" )

    def getPackageIdentifier( self, module_name ):
        return module_name.replace( ".", "__" )

    def getPackageCode( self, package_name ):
        package_identifier = self.getPackageIdentifier( package_name )

        header = CodeTemplates.package_header_template % {
            "package_identifier" : package_identifier,
        }

        body = CodeTemplates.package_body_template % {
            "package_name"       : package_name,
            "package_identifier" : package_identifier,
        }

        return header, body

    def getModuleCode( self, context, stand_alone, module_name, codes, doc_identifier, filename_identifier ):
        functions_decl = self.getFunctionsDecl( context = context )
        functions_code = self.getFunctionsCode( context = context )

        module_var_names = context.getGlobalVariableNames()

        # These ones are used in the init code to set these variables to their values
        # after module creation.
        module_var_names.add( "__file__" )
        module_var_names.add( "__doc__" )

        if module_name.find( "." ) != -1:
            module_var_names.add( "__package__" )

        module_identifier = self.getModuleIdentifier( module_name )

        module_globals = "\n".join( [ """static PyObjectGlobalVariable _mvar_%s_%s( &_module_%s, &%s );""" % ( module_identifier, var_name, module_identifier, context.getConstantHandle( constant = var_name ).getCode() ) for var_name in sorted( module_var_names ) ] )

        # Make sure that _python_str_angle_module is available to the template
        context.getConstantHandle( constant = "<module>" )

        if module_name.find( "." ) == -1:
            package_name = None

            module_inits = CodeTemplates.module_plain_init_template % {
                "module_identifier" : module_identifier,
                "file_identifier"   : filename_identifier.getCode(),
                "doc_identifier"    : doc_identifier.getCode(),

            }

        else:
            package_name = module_name[:module_name.rfind( "." )]

            module_inits = CodeTemplates.module_package_init_template % {
                "module_identifier"       : module_identifier,
                "module_name"             : self.getConstantCode( context = context, constant = module_name.split(".")[-1] ),
                "file_identifier"         : filename_identifier.getCode(),
                "doc_identifier"          : doc_identifier.getCode(),
                "package_name_identifier" : self.getConstantCode( context = context, constant = package_name ),
                "package_identifier"      : self.getPackageIdentifier( package_name )
            }

        if stand_alone:
            header = CodeTemplates.global_copyright % { "name" : module_name }
            constant_init = context.global_context.getConstantCode()
        else:
            header = CodeTemplates.module_header % {
                "name" : module_name,
            }
            constant_init = ""

        module_code = CodeTemplates.module_body_template % {
            "module_name"           : module_name,
            "module_identifier"     : module_identifier,
            "module_functions_decl" : functions_decl,
            "module_functions_code" : functions_code,
            "module_globals"        : module_globals,
            "module_inits"          : module_inits,
            "file_identifier"       : filename_identifier.getCode(),
            "module_code"           : _indentedCode( codes, 8 ),
        }

        return header + constant_init + module_code

    def getModuleDeclarationCode( self, module_name ):
        return CodeTemplates.module_header_template % {
            "module_name"       : module_name,
            "module_identifier" : self.getModuleIdentifier( module_name ),
        }

    def getMainCode( self, codes, other_modules ):
        module_inittab = []

        for other_module in other_modules:
            module_name = other_module.getFullName()

            module_inittab.append (
                CodeTemplates.module_inittab_entry % {
                    "module_name"       : module_name,
                    "module_identifier" : self.getModuleIdentifier( module_name ),
                }
            )

        main_code = CodeTemplates.main_program % {
            "module_inittab" : _indentedCode( module_inittab, 4 )
        }

        return codes + main_code


    def getFunctionsCode( self, context ):
        result = ""

        for contraction_info in sorted( context.getContractionsCodes(), key = lambda x : x[0].getCodeName() ):
            contraction, contraction_identifier, contraction_context, loop_var_codes, contraction_code, contraction_conditions, contraction_iterateds = contraction_info

            if contraction.isExpressionGenerator():
                result += self.getGeneratorExpressionCode(
                    context              = context,
                    generator            = contraction,
                    generator_identifier = contraction_identifier,
                    generator_code       = contraction_code,
                    generator_conditions = contraction_conditions,
                    generator_iterateds  = contraction_iterateds,
                    loop_var_codes       = loop_var_codes
                )
            else:
                result += self.getContractionCode(
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
            result += self.getFunctionCode(
                context        = function_context,
                function       = function,
                function_codes = function_codes
            )

        classes_infos = context.getClassesCodes()

        for class_def, ( class_context, class_codes ) in sorted( classes_infos.items(), key = lambda x : x[0].getCodeName() ):
            result += self.getClassCode(
                context     = class_context,
                class_def   = class_def,
                class_codes = class_codes
            )

        for lambda_def, lambda_codes, lambda_context in sorted( context.getLambdasCodes(), key = lambda x : x[0].getCodeName() ):
            result += self.getLambdaCode(
                context      = lambda_context,
                lambda_def   = lambda_def,
                lambda_codes = lambda_codes
            )

        return result

    def getFunctionsDecl( self, context ):
        result = ""

        for contraction_info in sorted( context.getContractionsCodes(), key = lambda x : x[0].getCodeName() ):
            contraction, contraction_identifier, _contraction_context, _loop_var_code, _contraction_code, _contraction_conditions, _contraction_iterateds = contraction_info
            if contraction.isExpressionGenerator():
                result += self.getGeneratorExpressionDecl(
                    generator_expression = contraction,
                    generator_identifier = contraction_identifier
                )
            else:
                result += self.getContractionDecl(
                    contraction            = contraction,
                    contraction_identifier = contraction_identifier
                )

        functions_infos = context.getFunctionsCodes()

        for function, function_context, _function_codes in sorted( functions_infos, key = lambda x : x[0].getCodeName() ):
            result += self.getFunctionDecl(
                context  = function_context,
                function = function,
            )

        classes_infos = context.getClassesCodes()

        for class_def, ( _class_context, _class_codes ) in sorted( classes_infos.items(), key = lambda x : x[0].getCodeName() ):
            result += self.getClassDecl(
                context   = context,
                class_def = class_def,
            )

        for lambda_def, _lambda_code, _lambda_context in sorted( context.getLambdasCodes(), key = lambda x : x[0].getCodeName() ):
            result += self.getLambdaDecl(
                lambda_def = lambda_def
            )

        return result

    def _getContractionParameters( self, contraction ):
        contraction_parameters = [ "PyObject *iterated" ]

        for variable in contraction.getClosureVariables():
            assert variable.isClosureReference()

            contraction_parameters.append( self._getClosureVariableDecl( variable = variable, from_context = False, for_argument = True  ) )

        return contraction_parameters

    def getContractionDecl( self, contraction, contraction_identifier ):
        contraction_parameters = self._getContractionParameters(
            contraction = contraction
        )

        return CodeTemplates.contraction_decl_template % {
           "contraction_identifier" : contraction_identifier,
           "contraction_parameters" : ", ".join( contraction_parameters )
        }

    def getContractionCode( self, contraction, contraction_context, contraction_identifier, loop_var_codes, contraction_code, contraction_conditions, contraction_iterateds ):
        contraction_parameters = self._getContractionParameters(
            contraction = contraction
        )

        if contraction.isListContraction():
            contraction_decl_template = CodeTemplates.list_contration_var_decl
            contraction_loop = CodeTemplates.list_contraction_loop_production % {
                "contraction_body" : contraction_code.getCodeTemporaryRef(),
            }
        elif contraction.isSetContraction():
            contraction_decl_template = CodeTemplates.set_contration_var_decl
            contraction_loop = CodeTemplates.set_contraction_loop_production % {
                "contraction_body" : contraction_code.getCodeTemporaryRef(),
            }

        elif contraction.isDictContraction():
            contraction_decl_template = CodeTemplates.dict_contration_var_decl
            contraction_loop = CodeTemplates.dict_contraction_loop_production % {
                "key_identifier" : contraction_code[0].getCodeTemporaryRef(),
                "value_identifier" : contraction_code[1].getCodeTemporaryRef()
            }

        else:
            assert False, contraction

        local_var_decl = []

        for variable in contraction.getProvidedVariables():
            if not variable.isClosureReference():
                local_var_decl.append( self._getLocalVariableInitCode( contraction_context, variable, in_context = False ) )


        contraction_var_decl = contraction_decl_template % {
            "local_var_decl" : _indentedCode( local_var_decl, 4 )
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
            "contraction_var_decl"   : _indentedCode( contraction_var_decl.split( "\n" ), 4 )
        }

    def getContractionIterValueIdentifier( self, context, index ):
        if not context.isGeneratorExpression():
            return Identifier( "_python_contraction_iter_value_%d" % index, 0 )
        else:
            return Identifier( "_python_genexpr_iter_value", 0 )

    def getGeneratorExpressionDecl( self, generator_expression, generator_identifier ):
        return self._getFunctionDecl(
            function_identifier = generator_identifier,
            parameters          = None,
            closure_variables   = generator_expression.getClosureVariables(),
            decorators          = (),
            is_generator        = True
        )

    def _getFunctionCreationArgs( self, decorators, parameters, closure_variables, is_generator ):
        if decorators:
            result = [ "PyObject *decorator_%d" % ( d + 1 ) for d in range( len( decorators ) ) ]
        else:
            result = []

        if is_generator:
            result += [ "PyObject *iterator" ]

        if parameters is not None:
            for defaulted_variable in parameters.getDefaultParameterVariables():
                default_par_code_name = self._getDefaultParameterCodeName( defaulted_variable )

                result.append( "PyObject *%s" % default_par_code_name )

        for closure_variable in closure_variables:
            result.append( "PyObjectSharedLocalVariable &python_closure_%s" % closure_variable.getName() )

        return ", ".join( result )

    def _getFunctionDecl( self, function_identifier, decorators, parameters, closure_variables, is_generator ):
        return CodeTemplates.function_decl_template % {
            "function_identifier"    : function_identifier,
            "function_creation_args" : self._getFunctionCreationArgs(
                decorators        = decorators,
                parameters        = parameters,
                closure_variables = closure_variables,
                is_generator      = is_generator
            )
        }

    def _getLocalVariableInitCode( self, context, variable, init_from = None, needs_no_free = False, in_context = False, shared = False, mangle_name = None ):
        shared = shared or variable.isShared()

        if shared:
            result = "PyObjectSharedLocalVariable"
        elif context.hasLocalsDict():
            result = "PyObjectLocalDictVariable"
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

            if context.hasLocalsDict():
                result += "locals_dict.asObject(), ";

            result += "%s" % context.getConstantHandle( constant = store_name ).getCode()

            if init_from is not None:
                result += ", " + init_from

                if context.hasLocalsDict():
                    assert not needs_no_free
                else:
                    if not needs_no_free:
                        result += ", true"

            if needs_no_free:
                result += ", false"

            result += " )"

        result += ";"

        return result

    def _getDefaultParameterCodeName( self, variable ):
        if variable.isNestedParameterVariable():
            return "default_values_%s" % "_".join( variable.getParameterNames() )
        else:
            return "default_value_%s" % variable.getName()

    def _getParameterParsingCode( self, context, function_name, parameters ):
        function_context_decl = []
        function_context_copy = []
        function_context_free = []

        function_parameter_variables = parameters.getVariables()

        top_level_parameters = parameters.getTopLevelVariables()

        parameter_parsing_code = "\n".join( [ "PyObject *_python_par_" + variable.getName() + " = NULL;" for variable in parameters.getAllVariables() ] )

        parameter_release_codes = [ "Py_XDECREF( _python_par_" + variable.getName() + " );" for variable in parameters.getAllVariables() ]

        parameter_parsing_code += CodeTemplates.parse_argument_template_take_counts % {
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
                    "parameter_names_tuple" : self.getConstantCode( context = context, constant = tuple( variable.getName() for variable in function_parameter_variables ) )
                }

            check_template = CodeTemplates.parse_argument_template_check_counts_without_list_star_arg if parameters.getListStarArgVariable() is None else CodeTemplates.parse_argument_template_check_counts_with_list_star_arg
            parameter_parsing_code += check_template % {
                "function_name"             : function_name,
                "top_level_parameter_count" : len( top_level_parameters ),
                "required_parameter_count"  : len( top_level_parameters ) - parameters.getDefaultParameterCount(),
            }



        if top_level_parameters:
            parameter_parsing_code += """// Copy normal parameter values given as part of the args list to the respective variables\n"""

            for count, variable in enumerate( top_level_parameters ):
                parameter_parsing_code += CodeTemplates.parse_argument_template2 % {
                    "parameter_name"     : variable.getName(),
                    "parameter_position" : count
                }

        if parameters.getListStarArgVariable() is not None:
            parameter_parsing_code += CodeTemplates.parse_argument_template_copy_list_star_args % {
                "list_star_parameter_name"  : parameters.getListStarArgName(),
                "top_level_parameter_count" : len( top_level_parameters )
            }

        if top_level_parameters:
            parameter_parsing_code += """// Copy given dictionary values to the the respective variables\n"""

        if parameters.getDictStarArgVariable() is not None:
            parameter_parsing_code += CodeTemplates.parse_argument_template_dict_star_copy % {
                "dict_star_parameter_name" : parameters.getDictStarArgName(),
            }

            for variable in top_level_parameters:
                if not variable.isNestedParameterVariable():
                    parameter_parsing_code += CodeTemplates.parse_argument_template_check_dict_parameter_with_star_dict % {
                        "function_name"            : function_name,
                        "parameter_name"           : variable.getName(),
                        "parameter_name_object"    : self.getConstantCode( constant = variable.getName(), context = context ),
                        "dict_star_parameter_name" : parameters.getDictStarArgName(),
                    }
        else:
            for variable in top_level_parameters:
                if not variable.isNestedParameterVariable():
                    parameter_parsing_code += CodeTemplates.parse_argument_template_check_dict_parameter_without_star_dict % {
                        "function_name"         : function_name,
                        "parameter_name"        : variable.getName(),
                        "parameter_identifier"  : self.getVariableHandle( variable = variable, context = context ).getCode(),
                        "parameter_name_object" : self.getConstantCode( constant = variable.getName(), context = context )
                    }

        if parameters.hasDefaultParameters():
            parameter_parsing_code += "// Assign values not given to defaults\n"

            for var_count, variable in enumerate( parameters.getDefaultParameterVariables() ):
                if not variable.isNestedParameterVariable():
                    parameter_parsing_code += CodeTemplates.parse_argument_template_copy_default_value % {
                        "parameter_name"     : variable.getName(),
                        "default_identifier" : context.getDefaultHandle( variable.getName() ).getCode()
                    }


        def unPackNestedParameterVariables( variables, recursion ):
            result = ""

            for var_count, variable in enumerate( variables ):
                if variable.isNestedParameterVariable():
                    if recursion == 1 and variable in parameters.getDefaultParameterVariables():
                        assign_source = Identifier( "_python_par_%s ? _python_par_%s : _python_context->%s" % ( variable.getName(), variable.getName(), self._getDefaultParameterCodeName( variable ) ), 0 )
                    else:
                        assign_source = Identifier( "_python_par_%s" % variable.getName(), 0 )

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
            default_par_code_name = self._getDefaultParameterCodeName( defaulted_variable )

            function_context_decl.append( "PyObject *%s;" % default_par_code_name )
            function_context_copy.append( "_python_context->%s = %s;" % ( default_par_code_name, default_par_code_name ) )
            function_context_free.append( "Py_DECREF( _python_context->%s );" % default_par_code_name )

        parameter_parsing_codes = parameter_parsing_code.split( "\n" )

        return function_parameter_variables, function_context_decl, function_context_copy, function_context_free, parameter_parsing_codes, parameter_release_codes

    def _getDecoratorsCallCode( self, decorators, context ):
        def _getCall( count ):
            return self.getFunctionCallCode(
                context              = context,
                function_identifier  = Identifier( "decorator_%d" % count, 0 ),
                argument_tuple       = self.getSequenceCreationCode(
                    sequence_kind       = "tuple",
                    element_identifiers = [ Identifier( "result", 1 ) ],
                    context             = context
                ),
                argument_dictionary  = Identifier( "NULL", 0 ),
                star_dict_identifier = None,
                star_list_identifier = None
            )


        decorator_calls = [ "result = %s;" % _getCall( count + 1 ).getCode() for count in range( len( decorators ) ) ]

        return decorator_calls


    def _getGeneratorFunctionCode( self, context, function_name, function_identifier, parameters, closure_variables, user_variables, decorators, function_codes, function_filename, function_doc ):
        function_parameter_variables, function_context_decl, function_context_copy, function_context_free, parameter_parsing_codes, parameter_release_codes = self._getParameterParsingCode(
            context                = context,
            function_name          = function_name,
            parameters             = parameters,
        )

        if function_parameter_variables:
            parameter_object_decl = ", " + ", ".join( [ "PyObject *_python_par_" + variable.getName() for variable in function_parameter_variables ] )
            parameter_object_list = ", " + ", ".join( [ "_python_par_" + variable.getName() for variable in function_parameter_variables ] )
        else:
            parameter_object_decl = ""
            parameter_object_list = ""

        function_parameter_decl = []
        parameter_context_assign = []
        function_var_inits = []

        for variable in function_parameter_variables:
            function_parameter_decl.append( self._getLocalVariableInitCode( context, variable, in_context = True ) )
            parameter_context_assign.append( "_python_context->python_var_" + variable.getName() + " = _python_par_" + variable.getName() + ";" )
            parameter_context_assign.append( "_python_context->python_var_%s.setVariableName( %s );" % ( variable.getName(), self.getConstantCode( constant = variable.getName(), context = context ) ) )


        local_var_decl = []

        for user_variable in user_variables:
            local_var_decl.append( self._getLocalVariableInitCode( context, user_variable, in_context = True ) )
            function_var_inits.append( "_python_context->python_var_%s.setVariableName( %s );" % ( user_variable.getName(), context.getConstantHandle( constant = user_variable.getName() ).getCode() ) )

        for closure_variable in closure_variables:
            function_context_decl.append( self._getLocalVariableInitCode( context, variable = closure_variable, in_context = True, shared = True ) )
            function_context_copy.append( "_python_context->python_closure_%s.shareWith( python_closure_%s );" % ( closure_variable.getName(), closure_variable.getName() ) )

        function_creation_args = self._getFunctionCreationArgs(
            decorators        = decorators,
            parameters        = parameters,
            closure_variables = closure_variables,
            is_generator      = False
        )

        function_decorator_calls = self._getDecoratorsCallCode(
            decorators = decorators,
            context    = context
        )

        function_doc = self.getConstantHandle( context = context, constant = function_doc ).getCode()

        result = CodeTemplates.genfunc_context_body_template % {
            "function_identifier"            : function_identifier,
            "function_common_context_decl"   : _indentedCode( function_context_decl, 4 ),
            "function_instance_context_decl" : _indentedCode( function_parameter_decl + local_var_decl, 4 ),
            "function_context_free"          : _indentedCode( function_context_free, 8 ),
        }

        result += CodeTemplates.genfunc_yielder_template % {
            "function_name"       : function_name,
            "function_identifier" : function_identifier,
            "function_body"       : _indentedCode( function_codes, 8 ),
            "function_var_inits"  : _indentedCode( function_var_inits, 8 ),
            "module_identifier"   : self.getModuleAccessCode( context = context ),
            "name_identifier"     : self.getConstantCode( context = context, constant = function_name ),
            "filename_identifier" : self.getConstantCode( context = context, constant = function_filename )
        }

        result += CodeTemplates.genfunc_function_template % {
            "function_name"          : function_name,
            "function_name_obj"      : self.getConstantCode( context = context, constant = function_name ),
            "function_identifier"    : function_identifier,
            "parameter_parsing_code" : _indentedCode( parameter_parsing_codes, 4 ),
            "parameter_release_code" : _indentedCode( parameter_release_codes, 4 ),
            "parameter_context_assign" : _indentedCode( parameter_context_assign, 4 ),
            "parameter_object_decl"  : parameter_object_decl,
            "parameter_object_list"  : parameter_object_list,
            "function_context_copy"  : _indentedCode( function_context_copy, 4 ),
            "module"                 : self.getModuleAccessCode( context = context ),
        }


        result += CodeTemplates.make_genfunc_with_context_template % {
            "function_name"              : function_name,
            "function_name_obj"          : self.getConstantCode( context = context, constant = function_name ),
            "function_identifier"        : function_identifier,
            "function_creation_args"     : function_creation_args,
            "function_decorator_calls"   : _indentedCode( function_decorator_calls, 4 ),
            "function_context_copy"      : _indentedCode( function_context_copy, 4 ),
            "function_doc"               : function_doc,
            "module"                     : self.getModuleAccessCode( context = context ),
        }

        return result

    def _getFunctionCode( self, context, function_name, function_identifier, parameters, closure_variables, user_variables, decorators, function_codes, function_filename, function_doc ):
        function_parameter_variables, function_context_decl, function_context_copy, function_context_free, parameter_parsing_codes, parameter_release_codes = self._getParameterParsingCode(
            context                = context,
            function_name          = function_name,
            parameters             = parameters,
        )

        function_parameter_decl = [ self._getLocalVariableInitCode( context, variable, in_context = False, init_from = "_python_par_" + variable.getName() ) for variable in function_parameter_variables ]

        if function_parameter_variables:
            parameter_object_decl = ", " + ", ".join( [ "PyObject *_python_par_" + variable.getName() for variable in function_parameter_variables ] )
            parameter_object_list = ", " + ", ".join( [ "_python_par_" + variable.getName() for variable in function_parameter_variables ] )
        else:
            parameter_object_decl = ""
            parameter_object_list = ""


        for closure_variable in closure_variables:
            function_context_decl.append( "PyObjectSharedLocalVariable python_closure_%s;" % closure_variable.getName() )
            function_context_copy.append( "_python_context->python_closure_%s.shareWith( python_closure_%s );" % ( closure_variable.getName(), closure_variable.getName() ) )


        function_creation_args = self._getFunctionCreationArgs(
            decorators        = decorators,
            parameters        = parameters,
            closure_variables = closure_variables,
            is_generator      = False
        )

        # User local variable initializations
        local_var_inits = [ self._getLocalVariableInitCode( context, variable ) for variable in user_variables ]

        function_decorator_calls = self._getDecoratorsCallCode(
            decorators = decorators,
            context    = context
        )

        function_doc = self.getConstantHandle( context = context, constant = function_doc ).getCode()

        if context.hasLocalsDict():
            function_locals = CodeTemplates.function_dict_setup.split("\n") + function_parameter_decl + local_var_inits
        else:
            function_locals = function_parameter_decl + local_var_inits


        result = ""

        if function_context_decl:
            result += CodeTemplates.function_context_body_template % {
                "function_identifier"   : function_identifier,
                "function_context_decl" : _indentedCode( function_context_decl, 4 ),
                "function_context_free" : _indentedCode( function_context_free, 4 ),
            }

            context_access_template = CodeTemplates.function_context_access_template % {
                "function_identifier" : function_identifier,
            }
        else:
            context_access_template = CodeTemplates.function_context_unused_template

        result += CodeTemplates.function_body_template % {
            "function_name"           : function_name,
            "function_identifier"     : function_identifier,
            "context_access_template" : context_access_template,
            "parameter_parsing_code"  : _indentedCode( parameter_parsing_codes, 4 ),
            "parameter_release_code"  : _indentedCode( parameter_release_codes, 4 ),
            "parameter_object_decl"   : parameter_object_decl,
            "parameter_object_list"   : parameter_object_list,
            "function_locals"         : _indentedCode( function_locals, 8 ),
            "function_body"           : _indentedCode( function_codes, 8 ),
            "module_identifier"       : self.getModuleAccessCode( context = context ),
            "name_identifier"         : self.getConstantCode( context = context, constant = function_name ),
            "filename_identifier"     : self.getConstantCode( context = context, constant = function_filename ),
        }

        if function_context_decl:
            result += CodeTemplates.make_function_with_context_template % {
                "function_name"              : function_name,
                "function_name_obj"          : self.getConstantCode( context = context, constant = function_name ),
                "function_identifier"        : function_identifier,
                "function_creation_args"     : function_creation_args,
                "function_decorator_calls"   : _indentedCode( function_decorator_calls, 4 ),
                "function_context_copy"      : _indentedCode( function_context_copy, 4 ),
                "function_doc"               : function_doc,
                "module"                     : self.getModuleAccessCode( context = context ),
            }
        else:
            result += CodeTemplates.make_function_without_context_template % {
                "function_name"              : function_name,
                "function_name_obj"          : self.getConstantCode( context = context, constant = function_name ),
                "function_identifier"        : function_identifier,
                "function_creation_args"     : function_creation_args,
                "function_decorator_calls"   : _indentedCode( function_decorator_calls, 4 ),
                "function_doc"               : function_doc,
                "module"                     : self.getModuleAccessCode( context = context ),
            }

        return result

    def getGeneratorExpressionCode( self, context, generator, generator_identifier, generator_code, generator_conditions, generator_iterateds, loop_var_codes ):
        function_name     = "<" + generator.getFullName() + ">"
        function_filename = generator.getParentModule().getFilename()

        function_context_decl = []
        function_context_copy = []
        function_context_release = []

        function_creation_args = [ "PyObject *iterated" ]

        for closure_variable in generator.getClosureVariables():
            function_context_decl.append( "PyObjectSharedLocalVariable python_closure_%s;" % closure_variable.getName() )
            function_context_copy.append( "_python_context->python_closure_%s.shareWith( python_closure_%s );" % ( closure_variable.getName(), closure_variable.getName() ) )

            function_creation_args.append( "PyObjectSharedLocalVariable &python_closure_%s" % closure_variable.getName() )

        # Into the context the provided variables must go:
        for variable in generator.getProvidedVariables():
            if not variable.isClosureReference():
                function_context_decl.append( "PyObjectLocalVariable python_var_%s;" % variable.getName() )

        result = ""

        result += CodeTemplates.genexpr_context_body_template % {
            "function_identifier"      : generator_identifier,
            "function_context_decl"    : "\n    ".join( function_context_decl ),
            "function_context_release" : "\n    ".join( function_context_release ),
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


        line_number_code = self.getCurrentLineCode( generator.getSourceReference() ) if Options.shallHaveStatementLines() else ""

        result += CodeTemplates.genexpr_function_template % {
            "function_name"              : function_name,
            "function_identifier"        : generator_identifier,
            "function_context_decl"      : "\n    ".join( function_context_decl ),
            "function_context_copy"      : "\n    ".join( function_context_copy ),
            "function_context_release"   : "\n    ".join( function_context_release ),
            "iterator_count"             : len( generator.getTargets() ),
            "iterator_making"            : iterator_making,
            "iterator_value_assign"      : iterator_value_assign,
            "function_body"              : self.getReturnCode( context = context, identifier = generator_code ),
            "module"                     : self.getModuleAccessCode( context = context ),
            "name_identifier"            : self.getConstantCode( context = context, constant = function_name ),
            "file_identifier"            : self.getConstantCode( context = context, constant = function_filename ),
            "line_number_code"           : line_number_code,
        }

        full_name = generator.getFullName()

        result += CodeTemplates.make_genexpr_with_context_template % {
            "function_name"              : full_name,
            "function_name_obj"          : self.getConstantCode( context = context, constant = full_name ),
            "function_identifier"        : generator_identifier,
            "function_creation_args"     : ", ".join( function_creation_args ),
            "function_context_copy"      : "\n    ".join( function_context_copy ),
            "function_doc"               : "Py_None",
            "iterator_count"             : len( generator.getTargets() ),
            "module"                     : self.getModuleAccessCode( context = context ),
        }

        return result


    def getFunctionDecl( self, context, function ):
        return self._getFunctionDecl(
            function_identifier = function.getCodeName(),
            decorators          = function.getDecorators(),
            parameters          = function.getParameters(),
            closure_variables   = function.getClosureVariables(),
            is_generator        = False
        )


    def getFunctionCode( self, context, function, function_codes ):
        if not function.isGenerator():
            return self._getFunctionCode(
                context              = context,
                function_name        = function.getFunctionName(),
                function_identifier  = function.getCodeName(),
                parameters           = function.getParameters(),
                closure_variables    = function.getClosureVariables(),
                user_variables       = function.getUserLocalVariables(),
                decorators           = function.getDecorators(),
                function_filename    = function.getParentModule().getFilename(),
                function_codes       = function_codes,
                function_doc         = function.getDoc()
            )
        else:
            return self._getGeneratorFunctionCode(
                context              = context,
                function_name        = function.getFunctionName(),
                function_identifier  = function.getCodeName(),
                parameters           = function.getParameters(),
                closure_variables    = function.getClosureVariables(),
                user_variables       = function.getUserLocalVariables(),
                decorators           = function.getDecorators(),
                function_filename    = function.getParentModule().getFilename(),
                function_codes       = function_codes,
                function_doc         = function.getDoc()
            )


    def getLambdaDecl( self, lambda_def ):
        return self._getFunctionDecl(
            function_identifier = lambda_def.getCodeName(),
            parameters          = lambda_def.getParameters(),
            closure_variables   = lambda_def.getClosureVariables(),
            decorators          = (),
            is_generator        = False
        )

    def getLambdaCode( self, context, lambda_def, lambda_codes ):
        if not lambda_def.isGenerator():
            return self._getFunctionCode(
                context              = context,
                function_name        = "<lambda>",
                function_identifier  = lambda_def.getCodeName(),
                parameters           = lambda_def.getParameters(),
                user_variables       = lambda_def.getUserLocalVariables(),
                decorators           = (), # Lambda expressions can't be decorated.
                closure_variables    = lambda_def.getClosureVariables(),
                function_codes       = lambda_codes,
                function_filename    = lambda_def.getParentModule().getFilename(),
                function_doc         = None # Lambda expressions don't have doc strings
            )
        else:
            return self._getGeneratorFunctionCode(
                context              = context,
                function_name        = "<lambda>",
                function_identifier  = lambda_def.getCodeName(),
                parameters           = lambda_def.getParameters(),
                user_variables       = lambda_def.getUserLocalVariables(),
                decorators           = (), # Lambda expressions can't be decorated.
                closure_variables    = lambda_def.getClosureVariables(),
                function_codes       = lambda_codes,
                function_filename    = lambda_def.getParentModule().getFilename(),
                function_doc         = None # Lambda expressions don't have doc strings
            )


    def getCurrentLineCode( self, source_ref ):
        return "_current_line = %d;\n" % source_ref.getLineNumber()

    def getCurrentExceptionObjectCode( self ):
        return Identifier( "_exception.getObject()", 0 )

    def getTupleUnpackIteratorCode( self, recursion ):
        return TempVariableIdentifier( "tuple_iterator_%d" % recursion )

    def getTupleUnpackLeftValueCode( self, recursion, count ):
        return TempVariableIdentifier( "tuple_lvalue_%d_%d" % ( recursion, count ) )

    def _getClosureVariableDecl( self, variable, from_context, for_argument ):
        if for_argument:
            # Not every reference counts, therefore the above may be a weak reference.

            owner = variable.getOwner()

            if not owner.isParentVariableProvider():
                owner = owner.getParentVariableProvider()

            if owner.hasLocalsDict() and not for_argument:
                kind = "PyObjectLocalDictVariable"
            elif variable.getReferenced().isShared():
                kind = "PyObjectSharedLocalVariable"
            else:
                kind = "PyObjectLocalVariable"

            return "%s &_python_closure_%s" % (kind, variable.getName())
        else:
            assert False

    def getClassCreationCode( self, context, code_name, dict_identifier, bases_identifier, decorators ):
        args = decorators + [ bases_identifier, dict_identifier ]

        return Identifier(
            "MAKE_CLASS_%s( %s )" % (
                code_name,
                ", ".join( arg.getCodeTemporaryRef() for arg in args )
            ),
            1
        )

    def getClassDictCreationCode( self, context, class_def ):
        args = []

        for closure_variable in class_def.getClosureVariables():
            assert closure_variable.isClosureReference()

            handle = self.getVariableHandle( context = context, variable = closure_variable.getReferenced() )

            args.append( handle.getCode() )

        return Identifier( "%s( %s )" % ( class_def.getCodeName(), ", ".join( args ) ), 1 )

    def _getClassCreationArgs( self, context, class_def ):
        class_creation_args = [ "PyObject *decorator_%d" % ( d + 1 ) for d in range( len( class_def.getDecorators() ) ) ]
        class_creation_args.append( "PyObject *bases" )
        class_creation_args.append( "PyObject *dict" )

        class_dict_args = []

        for closure_variable in class_def.getClosureVariables():
            class_dict_args.append( self._getClosureVariableDecl( variable = closure_variable, from_context = False, for_argument = True  ) )

        return class_creation_args, class_dict_args

    def getClassDecl( self, context, class_def ):
        class_creation_args, class_dict_args = self._getClassCreationArgs(
            class_def = class_def,
            context   = context
        )

        return CodeTemplates.class_decl_template % {
            "class_identifier"    : class_def.getCodeName(),
            "class_dict_args"     : ", ".join( class_dict_args ),
            "class_creation_args" : ", ".join( class_creation_args )
        }

    def getClassCode( self, context, class_def, class_codes ):
        class_variables = class_def.getClassVariables()

        class_var_decl = []

        for class_variable in class_variables:
            class_var_decl.append( self._getLocalVariableInitCode( context, class_variable, in_context = False, mangle_name = class_def.getName() ) )

        class_creation_args, class_dict_args = self._getClassCreationArgs(
            class_def = class_def,
            context   = context
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
                class_dict_creation += '%s = MAKE_STATIC_METHOD( %s );\n' % ( var_identifier.getCode(), var_identifier.getCodeObject() )

        if context.hasLocalsDict():
            class_dict_creation += "PyObject *result = INCREASE_REFCOUNT( locals_dict.asObject() );"
        else:
            class_dict_creation += "PyObject *result = MAKE_LOCALS_DICT( %s );" % ", ".join( "&%s" % LocalVariableIdentifier( class_variable.getName() ).getCode() for class_variable in class_variables )

        class_decorator_calls = self._getDecoratorsCallCode(
            decorators = class_def.getDecorators(),
            context    = context
        )

        metaclass_variable = Variables.ModuleVariable(
            module = class_def.getParentModule(),
            variable_name = "__metaclass__"
        )

        return CodeTemplates.class_dict_template % {
            "class_identifier"      : class_def.getCodeName(),
            "class_name"            : self.getConstantHandle( constant = class_def.getName(), context = context ).getCode(),
            "module_name"           : self.getConstantCode( constant = context.getModuleName(), context = context ),
            "class_dict_args"       : ", ".join( class_dict_args ),
            "class_creation_args"   : ", ".join( class_creation_args ),
            "class_var_decl"        : _indentedCode( class_locals, 4 ),
            "class_dict_creation"   : _indentedCode( class_dict_creation.split("\n"), 8 ),
            "class_decorator_calls" : _indentedCode( class_decorator_calls, 4 ),
            "class_body"            : _indentedCode( class_codes, 8 ),
            "module_identifier"     : self.getModuleAccessCode( context = context ),
            "name_identifier"       : self.getConstantCode( context = context, constant = class_def.getName() ),
            "filename_identifier"   : self.getConstantCode( context = context, constant = class_def.getParentModule().getFilename() ),

            "metaclass_global_test" : self.getVariableTestCode(
                context  = context,
                variable = metaclass_variable
            ),
            "metaclass_global_var"  : self._getGlobalVariableHandle(
                context  = context,
                variable = metaclass_variable
            ).getCode(),
        }
