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
""" Generators for Python C/API Module Generator.

Then there is a module generator for module stuff. It wants a global generator to
put things into and produces a file. The idea is that module generators for
multiple modules may interact later.

There is one generator for global stuff. Global means that these things can be
used by all modules. This of course only really means global when we are compiling
a whole program nd have a set of modules.

"""

from Identifiers import Identifier, LocalVariableIdentifier, TempVariableIdentifier

import PythonOperators
import CodeTemplates
import Variables

class PythonGeneratorBase:
    def getConstantHandle( self, context, constant ):
        return context.getConstantHandle( constant )

    def getConstantCode( self, context, constant ):
        return self.getConstantHandle( context = context, constant = constant ).getCode()

    def getReturnCode( self, context, identifier ):
        if identifier is not None:
            return "return %s;" % identifier.getCodeExportRef()
        else:
            return "return;"

    def getYieldCode( self, context, identifier ):
        return "_python_context->yielded = %s; swapcontext( &_python_context->yielder_context, &_python_context->caller_context );" % identifier.getCodeExportRef()

    def getYieldTerminator( self ):
        return Identifier( "_sentinel_value", 0 )

    def getSequenceCreationCode( self, context, sequence_kind, element_identifiers ):
        assert sequence_kind in ( "tuple", "list" )

        if sequence_kind == "tuple":
            args = [ element_identifier.getCodeTemporaryRef() for element_identifier in element_identifiers ]
        else:
            args = [ element_identifier.getCodeExportRef() for element_identifier in element_identifiers ]

        return Identifier( "MAKE_%s( %s )" % ( sequence_kind.upper(), ", ".join( reversed( args ) ) ), 1 )

    def getSequenceConcatCode( self, seq1_identifier, seq2_identifier ):
        return Identifier( "SEQUENCE_CONCAT( %s, %s )" % ( seq1_identifier.getCodeTemporaryRef(), seq2_identifier.getCodeTemporaryRef() ), 1 )

    def getTupleConversionCode( self, sequence_identifier ):
        return Identifier( "TO_TUPLE( %s )" % sequence_identifier.getCodeTemporaryRef(), 1 )

    def getDictionaryCreationCode( self, context, keys, values ):
        args = []

        for key, value in reversed( zip( keys, values ) ):
            args.append( key.getCodeTemporaryRef() )
            args.append( value.getCodeTemporaryRef() )

        return Identifier( "MAKE_DICT( %s )" % ( ", ".join( args ) ), 1 )

    def getDictionaryMergeCode( self, dict1_identifier, dict2_identifier ):
        return Identifier( "MERGE_DICTS( %s, %s, false )" % ( dict1_identifier.getCodeTemporaryRef(), dict2_identifier.getCodeTemporaryRef() ), 1 )

    def getImportModuleCode( self, context, module_name, import_name, variable ):
        return self.getAssignmentCode(
            context    = context,
            variable   = variable,
            identifier = Identifier( """IMPORT_MODULE( %s, %s )""" % ( self.getConstantCode( constant = module_name, context = context ), self.getConstantCode( constant = import_name, context = context ) ), 1 )
        )

    def getImportModulesCode( self, context, imports ):
        code = ""

        for module_name, import_name, variable, _module_filename, _module_package in imports:
            code += self.getImportModuleCode(
                context     = context,
                module_name = module_name,
                import_name = import_name,
                variable    = variable
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

                import_code = """\
try {
%s
}
catch( _PythonException &_exception )
{
   _exception.setType( PyExc_ImportError);
   throw _exception;
}
""" % lookup_code

                module_imports.append( import_code )

        if not star_import:
            return CodeTemplates.import_from_template % {
                "module_name"    : module_name,
                "module_imports" : "\n    ".join( module_imports ),
                "import_list"    : self.getConstantHandle(
                    context  = context,
                    constant = tuple( object_names )
                    ).getCode()
                }
        else:
            return """   IMPORT_MODULE_STAR( %s, %s );""" % ( self.getModuleAccessCode( context = context ).getCode(), self.getConstantCode( constant = module_name, context = context ) )

    def getMaxIndexCode( self, context ):
        return Identifier( "PY_SSIZE_T_MAX", 0 )

    def getMinIndexCode( self, context ):
        return Identifier( "0", 0 )

    def getIndexCode( self, context, identifier ):
        return Identifier( "CONVERT_TO_INDEX( %s )" % identifier.getCodeTemporaryRef(), 0 )

    def getFunctionCallCode( self, context, function_identifier, argument_tuple, argument_dictionary ):
        return Identifier( "CALL_FUNCTION( %(named_args)s, %(pos_args)s, %(function)s )" % {
            "function"   : function_identifier.getCodeTemporaryRef(),
            "pos_args"   : argument_tuple.getCodeTemporaryRef(),
            "named_args" : argument_dictionary.getCodeTemporaryRef() if argument_dictionary.getCode() != "_python_dict_empty" else "NULL"
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

        result += "UNPACK_ITERATOR_CHECK( %s );\n" % iterator_identifier.getCodeObject()

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
        elif operator in ( "NUMBER_AND", "NUMBER_OR", "NUMBER_XOR" ):
            return Identifier( "%s( %s )" % ( operator, ", ".join( identifier_refs ) ), 1 )
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

        if contraction.isListContraction():
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

    def getConditionalExpressionCallCode( self, context, condition, codes_no, codes_yes ):
        check = "IF_TRUE"

        if codes_yes.getRefCount() == codes_no.getRefCount():
            return Identifier( "(CHECK_%s( %s ) ? %s : %s)" % ( check, condition.getCodeTemporaryRef(), codes_yes.getCodeObject(), codes_no.getCodeObject()), codes_yes.getRefCount() )
        else:
            return Identifier( "(CHECK_%s( %s ) ? %s : %s)" % ( check, condition.getCodeTemporaryRef(), codes_yes.getCodeExportRef(), codes_no.getCodeExportRef() ), 1 )

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
        # Remove the implicit "not" that Python always has in branch check.
        # check = "IF_TRUE" if check == "IF_FALSE" else "IF_FALSE"

        keyword = "if"

        result = ""

        for condition, branch_codes in zip( conditions, branches_codes ):
            if condition is not None:
                result += """\
%s ( CHECK_IF_TRUE( %s ) )
{
%s
}
""" % ( keyword, condition.getCodeTemporaryRef(), "\n    ".join( branch_codes ) )

                keyword = "else if"


        if len( conditions ) == len( branches_codes ) - 1:
            result += """\
else
{
%s
}""" % ( "\n    ".join( branches_codes[-1] ) )


        return result

    def getLoopContinueCode( self ):
        return "throw ContinueException();";

    def getLoopBreakCode( self ):
        return "throw BreakException();"

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

    def getConditionOrCode( self, context, conditions ):
        return "(%s)" % " || ".join( conditions )

    def getConditionAndCode( self, context, conditions ):
        return "(%s)" % " && ".join( conditions )

    def getConditionNotCode( self, context, condition ):
        return Identifier( "UNARY_NOT( %s )" % condition.getCodeTemporaryRef(), 0 )

    def getConditionCheckTrueCode( self, context, condition ):
        return Identifier( "CHECK_IF_TRUE( %s )" % condition.getCodeTemporaryRef(), 0 )

    def getTrueExpressionCode( self ):
        return Identifier( "true", 0 )

    def getSelectionOrCode( self, context, conditions ):
        result = " ?: ".join( [ "SELECT_IF_TRUE( %s )" % condition.getCodeExportRef() for condition in conditions[:-1] ] )

        return Identifier( "(%s ?: %s)" % ( result, conditions[-1].getCodeExportRef() ), 1 )

    def getSelectionAndCode( self, context, conditions ):
        result = " ?: ".join( [ "SELECT_IF_FALSE( %s )" % condition.getCodeExportRef() for condition in conditions[:-1] ] )

        return Identifier( "(%s ?: %s)" % ( result, conditions[-1].getCodeExportRef() ), 1 )

    def getAttributeAssignmentCode( self, context, target, attribute_name, identifier ):
        attribute = self.getConstantCode( context = context, constant = attribute_name )

        return "SET_ATTRIBUTE( %s, %s, %s );" % ( target.getCodeObject(), attribute, identifier.getCodeTemporaryRef() )

    def getAttributeDelCode( self, context, target, attribute_name ):
        attribute = self.getConstantCode( context = context, constant = attribute_name )

        return "DEL_ATTRIBUTE( %s, %s );" % ( target.getCodeObject(), attribute )

    def getSliceAssignmentCode( self, context, target, lower, upper, identifier  ):
        return "SET_SLICE( %s, %s, %s, %s );" % ( target.getCodeTemporaryRef(), lower.getCodeTemporaryRef(), upper.getCodeTemporaryRef(), identifier.getCodeTemporaryRef() )

    def getSliceDelCode( self, context, target, lower, upper ):
        return "DEL_SLICE( %s, %s, %s );" % ( target.getCodeTemporaryRef(), lower.getCodeTemporaryRef() if lower is not None else "Py_None", upper.getCodeTemporaryRef() if upper is not None else "Py_None" )

    def getBoolCreationCode( self, context, identifier ):
        return Identifier( "TO_BOOL( %s )" % identifier.getCodeTemporaryRef(), 0 )

    def getWithNames( self, context ):
        with_count = context.allocateWithNumber()

        return TempVariableIdentifier( "_python_with_context_%d" % with_count ), TempVariableIdentifier( "_python_with_value_%d" % with_count ),


    def getWithCode( self, context, body_codes, assign_codes, source_identifier, with_manager_identifier, with_value_identifier ):
        # TODO: Have a template for it.

        return """\
{
   _PythonExceptionKeeper _caught_%(with_count)d;

   PyObjectTemporary %(manager)s( %(source)s );

   // Should have a CALL_FUNCTION that does this for us.
   PyObject *_enter_result = PyObject_CallMethod( %(manager)s.asObject(), (char *)"__enter__", NULL );
   if (_enter_result == NULL)
   {
      throw _PythonException();
   }
   PyObjectTemporary %(value)s( _enter_result );
   try
   {
      %(assign)s
      %(body)s
   }
   catch ( _PythonException &_exception )
   {
      _caught_%(with_count)d.save( _exception );

      PyObject *exception_type  = _exception.getType();
      PyObject *exception_value = _exception.getObject();
      PyObject *exception_tb    = _exception.getTraceback();

      if ( exception_tb == NULL )
         exception_tb = Py_None;

      assert( exception_type );
      assert( exception_value );

      PyObject *result = PyObject_CallMethod( %(manager)s.asObject(), (char *)"__exit__",  (char *)"OOO", exception_type, exception_value, exception_tb, NULL );

      if ( result == NULL )
      {
         throw _PythonException();
      }

      if ( CHECK_IF_TRUE( result ))
      {
         PyErr_Clear();
      }
      else
      {
         _caught_%(with_count)d.rethrow();
      }
   }

   if ( _caught_%(with_count)d.isEmpty() )
   {
      PyObject *result = PyObject_CallMethod( %(manager)s.asObject(), (char *)"__exit__",  (char *)"OOO", Py_None, Py_None, Py_None, NULL );

      if ( result == NULL )
      {
         throw _PythonException();
      }
   }
}
""" % {
   "assign"     : assign_codes if assign_codes is not None else "",
   "body"       : "\n    ".join( body_codes ),
   "source"     : source_identifier.getCodeExportRef(),
   "manager"    : with_manager_identifier.getCode(),
   "value"      : with_value_identifier.getCode(),
   "with_count" : context.with_count,
}

    def getForLoopNames( self, context ):
        for_count = context.allocateForLoopNumber()

        return Identifier( "_python_for_loop_iterator_%d" % for_count, 0 ), Identifier(  "_python_for_loop_itervalue_%d" % for_count, 0 )

    def getForLoopCode( self, context, iterator, iter_name, iter_value, loop_var_code, loop_body_codes, loop_else_codes ):
        return """\
{
PyObjectTemporary %(loop_iter_identifier)s( %(iterator)s );
bool %(indicator_name)s = false;
while (1)
{
    try
    {

    PyObject *%(loop_value_identifier)s = ITERATOR_NEXT( %(loop_iter_identifier)s.asObject() );

    if (%(loop_value_identifier)s == NULL)
    {
       %(indicator_name)s = true;
       break;
    }

    try
    {
        %(loop_var_assignment_code)s

        Py_DECREF( %(loop_value_identifier)s );
    }
    catch(...)
    {
        Py_DECREF( %(loop_value_identifier)s );
        throw;
    }

    %(body)s

    }
    catch( ContinueException &e )
    { /* Nothing to do */
    }
    catch ( BreakException &e )
    { /* Break the loop */
       break;
    }
}

if ( %(indicator_name)s)
{
    %(else_codes)s
}
}""" % {
    "body"                     : "\n    ".join( loop_body_codes ),
    "else_codes"               : "\n    ".join( loop_else_codes ),
    "iterator"                 : iterator.getCodeExportRef(),
    "loop_iter_identifier"     : iter_name.getCode(),
    "loop_value_identifier"    : iter_value.getCode(),
    "loop_var_assignment_code" : loop_var_code,
    "indicator_name"  : "_python_for_loop_indicator_%d" % context.allocateForLoopNumber()
}

    def getWhileLoopCode( self, context, condition, loop_body_codes, loop_else_codes ):
        if not loop_else_codes:
            return """\
while (CHECK_IF_TRUE( %s ))
{
   try
   {
%s
    }
    catch( ContinueException &e )
    { /* Nothing to do */
    }
    catch ( BreakException &e )
    { /* Break the loop */
       break;
    }
}""" % ( condition.getCodeTemporaryRef(), "\n    ".join( loop_body_codes ) )
        else:
            return """\
  bool %(indicator_name)s = false;
while (CHECK_IF_TRUE( %(condition)s )) {
    try
    {
    %(indicator_name)s = true;
%(loop_body_codes)s
    }
    catch( ContinueException &e )
    { /* Nothing to do */
    }
    catch ( BreakException &e )
    { /* Break the loop */
       break;
    }
}
if (%(indicator_name)s == false)
{
%(loop_else_codes)s
}
""" % {
    "condition"       : condition.getCodeTemporaryRef(),
    "loop_body_codes" : "\n    ".join( loop_body_codes ),
    "loop_else_codes" : "\n    ".join( loop_else_codes ),
    "indicator_name"  : "_python_for_loop_indicator_%d" % context.allocateWhileLoopNumber()
}

    def getReferenceBumpCode( self, identifier ):
        return "INCREASE_REFCOUNT( %s )" % identifier

    def getVariableHandle( self, context, variable ):
        assert isinstance( variable, Variables.Variable ), variable

        var_name = variable.getName()

        if variable.isLocalVariable() or variable.isClassVariable():
            return context.getLocalHandle( var_name = variable.getName() )
        elif variable.isClosureReference():
            return context.getClosureHandle( var_name = variable.getName() )
        elif variable.isModuleVariable():
            context.addGlobalVariableNameUsage( var_name )

            return Identifier( "_mvar_%s_%s.asObject()" % ( context.getModuleName(), var_name ), 1 )
        else:
            assert False, variable

    def getAssignmentCode( self, context, variable, identifier ):
        assert isinstance( variable, Variables.Variable ), variable

        if variable.getOwner().isModule():
            var_name = variable.getName()

            context.addGlobalVariableNameUsage( var_name )

            return "_mvar_%s_%s.assign( %s );" % ( context.getModuleName(), var_name, identifier.getCodeTemporaryRef() )
        else:
            return "%s = %s;" % ( self.getVariableHandle( variable = variable, context = context ).getCode(), identifier.getCodeExportRef() )

    def getVariableDelCode( self, context, variable ):
        assert isinstance( variable, Variables.Variable ), variable

        if variable.isModuleVariable():
            var_name = variable.getName()

            context.addGlobalVariableNameUsage( var_name )

            return "_mvar_%s_%s.del();" % ( context.getModuleName(), var_name )
        else:
            return "%s.del();" % self.getVariableHandle( variable = variable, context = context ).getCode()

    def getVariableTestCode( self, context, variable ):
        assert isinstance( variable, Variables.Variable ), variable

        if variable.isModuleVariable():
            var_name = variable.getName()

            context.addGlobalVariableNameUsage( var_name )

            return "_mvar_%s_%s.isInitialized()" % ( context.getModuleName(), var_name )
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

        return """\
{
    PyObjectTemporary value = %s;
    PyObject *result = %s;

    if ( result != value.asObject() )
    {
        %s
    }

    Py_DECREF( result );
}""" % ( self.getVariableHandle( variable = variable, context = context ).getCodeExportRef(), self._getInplaceOperationCode( operator = operator, operand1 = value_identifier, operand2 = identifier ).getCode(), self.getAssignmentCode( variable = variable, context = context, identifier = result_identifier ) )

    def getInplaceSubscriptAssignmentCode( self, context, subscribed, subscript, operator, identifier ):
        value_identifier = Identifier( "value.asObject()", 0 )

        return """\
{
    PyObjectTemporary subscribed = %s;
    PyObjectTemporary subscript = %s;
    PyObjectTemporary value = LOOKUP_SUBSCRIPT( subscribed.asObject(), subscript.asObject() );

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
    PyObjectTemporary target = %s;
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
    PyObjectTemporary target = %s;
    PyObjectTemporary value = LOOKUP_SLICE( target.asObject(), %s, %s );
    PyObjectTemporary updated = %s;
    SET_SLICE( target.asObject(), %s, %s, updated.asObject() );
}""" % ( target.getCodeExportRef(), lower.getCode(), upper.getCode(), self._getInplaceOperationCode( operator = operator, operand1 = value_identifier, operand2 = identifier ).getCode(), lower.getCode(), upper.getCode() )

    def getTryFinallyCode( self, context, code_tried, code_final ):
        return CodeTemplates.try_finally_template % {
            "try_count"  : context.allocateTryNumber(),
            "tried_code" : "\n   ".join( code_tried ),
            "final_code" : "\n   ".join( code_final )
        }

    def getTryExceptCode( self, context, code_tried, exception_identifiers, exception_assignments, catcher_codes, else_code ):
        exception_code = []

        cond_keyword = "if"

        for exception_identifier, exception_assignment, code in zip( exception_identifiers, exception_assignments, catcher_codes ):
            if exception_identifier is not None:
                exception_code.append( "%s (_exception.matches(%s))" % ( cond_keyword, exception_identifier.getCodeTemporaryRef() ) )
            else:
                exception_code.append( "%s (true)" % cond_keyword )

            exception_code.append( "{" )

            if exception_assignment is not None:
                exception_code.append( exception_assignment )

            exception_code += [ "    " + line for line in code ]
            exception_code.append( "}" )

            cond_keyword = "else if"

        exception_code += [ "else", "{", "traceback = true; throw;", "}" ]

        if else_code is not None:
            return CodeTemplates.try_except_else_template % {
                "tried_code"     : "\n    ".join( code_tried ),
                "exception_code" : "\n    ".join( exception_code ),
                "else_code"      : "\n    ".join( else_code ),
                "tb_making"      : self.getTracebackMakerCall( context.getCodeName(), "_exception.getLine()" ),
                "except_count"   : context.allocateTryNumber()
            }
        else:
            return CodeTemplates.try_except_template % {
                "tried_code"     : "\n    ".join( code_tried ),
                "exception_code" : "\n    ".join( exception_code ),
                "tb_making"      : self.getTracebackMakerCall( context.getCodeName(), "_exception.getLine()" ),
            }


    def getRaiseExceptionCode( self, context, exception_type_identifier, exception_value_identifier, exception_tb_identifier, exception_tb_maker ):
        if exception_value_identifier is None and exception_tb_identifier is None:
            return "traceback = true; RAISE_EXCEPTION( %s, %s );" % ( exception_type_identifier.getCodeExportRef(), exception_tb_maker )
        elif exception_tb_identifier is None:
            return "traceback = true; RAISE_EXCEPTION( %s, %s, %s );" % ( exception_type_identifier.getCodeExportRef(), exception_value_identifier.getCodeExportRef(), exception_tb_maker )
        else:
            return "traceback = true; RAISE_EXCEPTION( %s, %s, %s );" % ( exception_type_identifier.getCodeExportRef(), exception_value_identifier.getCodeExportRef(), exception_tb_identifier.getCodeExportRef() )

    def getReRaiseExceptionCode( self, context ):
        return "traceback = true; throw;"

    def getAssertCode( self, context, condition_identifier, failure_identifier, exception_tb_maker ):
        if failure_identifier is None:
            return CodeTemplates.assertion_without_arg % {
                "condition" : condition_identifier.getCodeTemporaryRef(),
                "tb_maker"  : exception_tb_maker
            }
        else:
            return CodeTemplates.assertion_with_arg % {
                "condition"   : condition_identifier.getCodeTemporaryRef(),
                "failure_arg" : failure_identifier.getCodeExportRef(),
                "tb_maker"    : exception_tb_maker
            }

    def getLoadDirCode( self, context, provider ):
        if provider.isModule():
            return Identifier( "PyDict_Keys( %s )" % self.getLoadGlobalsCode( context = context, module = provider ).getCodeTemporaryRef(), 1 )
        else:
            return Identifier( "PyDict_Keys( %s )" % self.getLoadLocalsCode( context = context, provider = provider ).getCodeTemporaryRef(), 1 )

    def getLoadVarsCode( self, context, identifier ):
        return Identifier( "LOOKUP_VARS( %s )" % identifier.getCodeTemporaryRef(), 1 )

    def getLoadGlobalsCode( self, context, module ):
        return Identifier( "PyModule_GetDict( _module_%(module_name)s )" % { "module_name" : context.getModuleName() }, 0 )

    def getLoadLocalsCode( self, context, provider ):
        assert not provider.isModule()

        local_list = [ "&%s" % self.getVariableHandle( variable = variable, context = context ).getCode() for variable in provider.getVariables() if not variable.isModuleVariable() ]

        return Identifier( "MAKE_LOCALS_DICT( %s )" % ", ".join( local_list ), 1 )

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
if (%s)
{
   %s
}
""" % ( self.getHasKeyCode( context = context, source = source_identifier, key = key_identifier ).getCode(), var_assign_code )

        return code

    def getFutureFlagsCode( self, future_division, unicode_literals, absolute_import ):
        result = []

        if future_division:
            result.append( "CO_FUTURE_DIVISION" )

        if unicode_literals:
            result.append( "CO_FUTURE_UNICODE_LITERALS" )

        if absolute_import:
            result.append( "CO_FUTURE_ABSOLUTE_IMPORT" )

        if result:
            return " | ".join( result )
        else:
            return 0


    def getEvalCode( self, context, mode, exec_code, globals_identifier, locals_identifier, future_flags ):
        return Identifier( "EVAL_CODE( COMPILE_CODE( %s, %s, %s, %s ), %s, %s )" % (
            exec_code.getCodeTemporaryRef(),
            context.getConstantHandle( constant = "<string>" ).getCode(),
            context.getConstantHandle( constant = mode ).getCode(),
            future_flags,
            globals_identifier.getCodeTemporaryRef(),
            locals_identifier.getCodeTemporaryRef() if locals_identifier is not None else "NULL"
        ), 1 )

    def getExecLocalCode( self, context, exec_code, globals_identifier, future_flags, provider ):
        locals_identifier = Identifier( "locals.asObject()", 0 )

        return """\
{
    PyObjectTemporary locals = %s;

    EVAL_CODE( COMPILE_CODE( %s, %s, %s, %s ), %s, locals.asObject() );

    %s;
}""" % (
         self.getLoadLocalsCode( provider = provider, context = context ).getCodeExportRef(),
         exec_code.getCodeTemporaryRef(),
         context.getConstantHandle( constant = context.getModuleName() + "::exec" ).getCode(),
         context.getConstantHandle( constant = "exec" ).getCode(),
         future_flags,
         globals_identifier.getCodeTemporaryRef(),
         self.getStoreLocalsCode( context = context, source_identifier = locals_identifier, provider = provider )
       )

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
        return Identifier( "_module_%s" % context.getModuleName(), 0 )

    def getTracebackMaker( self, name ):
        return "MAKE_TRACEBACK_" + name

    def getTracebackMakerCall( self, name, line ):
        return "MAKE_TRACEBACK_" + name + "( %s )" % line

    def getTracebackAdder( self, name ):
        return "ADD_TRACEBACK_" + name

    def getModuleCode( self, context, stand_alone, module_name, codes, doc_identifier, filename_identifier ):
        header = CodeTemplates.global_copyright % { "name" : "module " + module_name }

        functions_decl = self.getFunctionsDecl( context = context )
        functions_code = self.getFunctionsCode( context = context )

        module_var_names = context.getGlobalVariableNames()

        # These ones are used in the init code to set these variables to their values
        # after module creation.
        module_var_names.add( "__file__" )
        module_var_names.add( "__doc__" )

        module_globals = "\n   ".join( [ """PyObjectGlobalVariable _mvar_%s_%s( &_module_%s, &%s );""" % ( module_name, var_name, module_name, context.getConstantHandle( constant = var_name ).getCode() ) for var_name in sorted( module_var_names ) ] );

        # Make sure that _python_str_angle_module is available to the template
        context.getConstantHandle( constant = "<module>" )

        if stand_alone:
            global_prelude = context.global_context.getPreludeCode()
            constant_init = context.global_context.getConstantCode()
            global_helper = context.global_context.getHelperCode()
        else:
            global_prelude = ""
            constant_init = ""
            global_helper = ""

        module_code = CodeTemplates.module_template % {
            "module_name"           : module_name,
            "file_identifier"       : filename_identifier.getCode(),
            "doc_identifier"        : doc_identifier.getCode(),
            "module_functions_decl" : functions_decl,
            "module_functions_code" : functions_code,
            "module_globals"        : module_globals,
            "module_code"           : "\n      ".join( codes ),
            "module_tb_adder"       : self.getTracebackAdder( context.getCodeName() ),
            "module_tb_maker"       : self.getTracebackMaker( context.getCodeName() )
        }

        return header + global_prelude + constant_init + global_helper + module_code

    def getMainCode( self, codes, other_modules ):
        header = CodeTemplates.global_copyright % { "name" : "module " + self.getName() }

        prepare_code = []

        for other_module in other_modules:
            module_package = other_module.getPackage()
            module_name = other_module.getName()

            if module_package is None:
                module_full_name = module_name
            else:
                module_full_name = module_package + "." + module_name

            prepare_code.append (
                CodeTemplates.prepare_other_module % {
                    "module_name"      : module_name,
                    "module_full_name" : module_full_name,
                }
            )

        main_code = CodeTemplates.main_program % {
            "prepare_modules" : "\n    ".join( prepare_code )
        }

        return header + codes + main_code


    def getFunctionsCode( self, context ):
        result = ""

        def myCompare( a, b ):
            return cmp( a[0].getCodeName(), b[0].getCodeName() )

        for contraction_info in sorted( context.getContractionsCodes(), cmp = myCompare ):
            contraction, contraction_identifier, _contraction_context, loop_var_codes, contraction_code, contraction_conditions, contraction_iterateds = contraction_info

            if contraction.isListContraction():
                result += self.getListContractionCode(
                    contraction            = contraction,
                    contraction_identifier = contraction_identifier,
                    contraction_code       = contraction_code,
                    contraction_conditions = contraction_conditions,
                    contraction_iterateds  = contraction_iterateds,
                    loop_var_codes         = loop_var_codes
                )
            else:
                result += self.getGeneratorExpressionCode(
                    context              = context,
                    generator            = contraction,
                    generator_identifier = contraction_identifier,
                    generator_code       = contraction_code,
                    generator_conditions = contraction_conditions,
                    generator_iterateds  = contraction_iterateds,
                    loop_var_codes       = loop_var_codes
                )

        functions_infos = context.getFunctionsCodes()

        for function, function_context, function_codes in sorted( functions_infos, cmp = myCompare ):
            result += self.getFunctionCode(
                context        = function_context,
                function       = function,
                function_codes = function_codes
            )

        classes_infos = context.getClassesCodes()

        for class_def, class_codes in sorted( classes_infos.iteritems(), cmp = myCompare ):
            result += self.getClassCode(
                context     = context,
                class_def   = class_def,
                class_codes = class_codes,
                module_name = context.getModuleName(),
            )

        for lambda_def, lambda_codes, lambda_context in sorted( context.getLambdasCodes(), cmp = myCompare ):
            result += self.getLambdaCode(
                context      = lambda_context,
                lambda_def   = lambda_def,
                lambda_codes = lambda_codes
            )

        return result

    def getFunctionsDecl( self, context ):
        result = ""

        def myCompare( a, b ):
            return cmp( a[0].getCodeName(), b[0].getCodeName() )


        for contraction_info in sorted( context.getContractionsCodes(), cmp = myCompare ):
            contraction, contraction_identifier, _contraction_context, _loop_var_code, _contraction_code, _contraction_conditions, _contraction_iterateds = contraction_info
            if contraction.isListContraction():
                result += self.getListContractionDecl(
                    contraction            = contraction,
                    contraction_identifier = contraction_identifier
                )
            else:
                result += self.getGeneratorExpressionDecl(
                    generator_expression = contraction,
                    generator_identifier = contraction_identifier
                )

        functions_infos = context.getFunctionsCodes()

        for function, function_context, _function_codes in sorted( functions_infos, cmp = myCompare ):
            result += self.getFunctionDecl(
                context  = function_context,
                function = function,
            )

        classes_infos = context.getClassesCodes()

        for class_def, _class_codes in sorted( classes_infos.iteritems(), cmp = myCompare ):
            result += self.getClassDecl(
                context   = context,
                class_def = class_def,
            )

        for lambda_def, _lambda_code, _lambda_context in sorted( context.getLambdasCodes(), cmp = myCompare ):
            result += self.getLambdaDecl(
                lambda_def = lambda_def
            )

        return result

    def _getListContractionParameters( self, contraction ):
        contraction_parameters = [ "PyObject *iterated" ]

        for variable in contraction.getClosureVariables():
            assert variable.isClosureReference()

            contraction_parameters.append( self._getClosureVariableDecl( variable = variable, from_context = False, for_argument = True  ) )

        return contraction_parameters

    def getListContractionDecl( self, contraction, contraction_identifier ):
        contraction_parameters = self._getListContractionParameters(
            contraction = contraction
        )

        return CodeTemplates.list_contraction_decl_template % {
           "contraction_identifier" : contraction_identifier,
           "contraction_parameters" : ", ".join( contraction_parameters )
        }

    def getListContractionCode( self, contraction, contraction_identifier, loop_var_codes, contraction_code, contraction_conditions, contraction_iterateds ):
        contraction_parameters = self._getListContractionParameters(
            contraction = contraction
        )

        contraction_loop = CodeTemplates.list_contraction_loop_production % {
            "contraction_body"           : contraction_code.getCodeTemporaryRef(),
        }

        contraction_iterateds.insert( 0, Identifier( "iterated", 0 ) )

        for count, ( contraction_condition, contraction_iterated, loop_var_code ) in enumerate( reversed( zip( contraction_conditions, contraction_iterateds, loop_var_codes ) ) ):
            contraction_loop = CodeTemplates.list_contraction_loop_iterated % {
                "contraction_loop"         : contraction_loop,
                "iter_count"               : len( loop_var_codes ) - count,
                "iterated"                 : contraction_iterated.getCodeTemporaryRef(),
                "loop_var_assignment_code" : loop_var_code,
                "contraction_condition"    : contraction_condition.getCode()
            }

        return CodeTemplates.list_contraction_code_template % {
            "contraction_identifier" : contraction_identifier,
            "contraction_parameters" : ", ".join( contraction_parameters ),
            "contraction_body"       : contraction_loop
        }

    def getContractionIterValueIdentifier( self, context, index ):
        if context.isListContraction():
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

    def _getLocalVariableInitCode( self, context, variable, init_from = None, needs_no_free = False, in_context = False, shared = False ):
        shared = shared or variable.isShared()
        result = "PyObjectLocalVariable" if not shared else "PyObjectSharedLocalVariable"

        var_name = variable.getName()

        result += " "

        if not in_context:
            result += "_"

        if variable.isClosureReference():
            result += "python_closure_%s" % var_name
        else:
            result += "python_var_%s" % var_name

        if not in_context:
            result += "( %s" % context.getConstantHandle( constant = var_name ).getCode()

            if init_from is not None:
                result += ", " + init_from

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

        function_parameter_decl = []

        parameter_parsing_code = ""

        top_level_parameters = parameters.getTopLevelVariables()
        parameter_variables = parameters.getVariables()

        if parameter_variables:
            function_parameter_decl.append( "// Declare normal parameter variables" )

            for variable in parameter_variables:
                function_parameter_decl.append( self._getLocalVariableInitCode( context, variable, in_context = context.isParametersViaContext() ) )

        def declareNestedParameterVariables( parameters ):
            for variable in parameters:
                if variable.isNestedParameterVariable():
                    function_parameter_decl.append( self._getLocalVariableInitCode( context, variable ) )

                    declareNestedParameterVariables( variable.getTopLevelVariables() )

        declareNestedParameterVariables( top_level_parameters )

        if parameters.isEmpty():
            parameter_parsing_code += CodeTemplates.parse_argument_template_refuse_parameters % {
                "function_name"             : function_name,
            }
        else:
            parameter_parsing_code += CodeTemplates.parse_argument_template_check_counts % {
                "function_name"             : function_name,
                "top_level_parameter_count" : len( top_level_parameters ),
                "required_parameter_count"  : len( top_level_parameters ) - parameters.getDefaultParameterCount(),
                "has_list_star_arg"         : "false" if parameters.getListStarArgVariable() is None else "true"
            }

        if top_level_parameters:
            parameter_parsing_code += """    // Copy normal parameter values given as part of the args list to the respective variables\n"""

            for count, variable in enumerate( top_level_parameters ):
                parameter_parsing_code += "   %s\n" % CodeTemplates.parse_argument_template2 % {
                    "parameter_identifier" : self.getVariableHandle( variable = variable, context = context ).getCode(),
                    "parameter_position"   : count
                }

        if parameters.getListStarArgVariable() is not None:
            parameter_parsing_code += CodeTemplates.parse_argument_template3 % {
                "list_star_parameter_identifier"  : self.getVariableHandle( variable = parameters.getListStarArgVariable(), context = context ).getCode(),
                "top_level_parameter_count"       : len( top_level_parameters )
            }

        if top_level_parameters:
            parameter_parsing_code += """    // Copy given dictionary values to the the respective variables\n"""

        if parameters.getDictStarArgVariable() is not None:
            dict_variable = self.getVariableHandle( variable = parameters.getDictStarArgVariable(), context = context )

            parameter_parsing_code += CodeTemplates.parse_argument_template_dict_star_copy % {
                "dict_star_parameter_identifier" : dict_variable.getCode(),
            }

            dictionary_name = dict_variable.getCodeObject()

            for variable in top_level_parameters:
                if not variable.isNestedParameterVariable():
                    parameter_parsing_code += CodeTemplates.parse_argument_template_check_dict_parameter_with_star_dict % {
                        "function_name"         : function_name,
                        "parameter_name"        : variable.getName(),
                        "parameter_identifier"  : self.getVariableHandle( variable = variable, context = context ).getCode(),
                        "parameter_name_object" : context.getConstantHandle( constant = variable.getName() ).getCode(),
                        "dictionary_variable"   : dictionary_name,
                    }
        else:
            parameter_name_objects = []

            for variable in top_level_parameters:
                if not variable.isNestedParameterVariable():
                    parameter_name_object = context.getConstantHandle( constant = variable.getName() ).getCode()

                    parameter_parsing_code += CodeTemplates.parse_argument_template_check_dict_parameter_without_star_dict % {
                        "function_name"         : function_name,
                        "parameter_name"        : variable.getName(),
                        "parameter_identifier"  : self.getVariableHandle( variable = variable, context = context ).getCode(),
                        "parameter_name_object" : parameter_name_object
                    }

                    parameter_name_objects.append( parameter_name_object )

            if top_level_parameters:
                parameter_parsing_code += CodeTemplates.parse_argument_template_check_dict_parameter_unused_without_star_dict % {
                    "function_name"          : function_name,
                    "parameter_name_objects" : ", ".join( parameter_name_objects )
                }

        if parameters.hasDefaultParameters():
            parameter_parsing_code += "    // Assign values not given to defaults\n"

            for var_count, variable in enumerate( parameters.getDefaultParameterVariables() ):
                if not variable.isNestedParameterVariable():
                    parameter_parsing_code += CodeTemplates.parse_argument_template_copy_default_value % {
                        "parameter_identifier"  : self.getVariableHandle( variable = variable, context = context ).getCode(),
                        "default_identifier"    : context.getDefaultHandle( variable.getName() ).getCode()
                    }


        def unPackNestedParameterVariables( variables, recursion ):
            result = ""

            for var_count, variable in enumerate( variables ):
                if variable.isNestedParameterVariable():
                    if recursion == 1 and variable in parameters.getDefaultParameterVariables():
                        assign_source = Identifier( "_python_var_%s.isInitialized() ? _python_var_%s.asObject() : _python_context->%s" % ( variable.getName(), variable.getName(), self._getDefaultParameterCodeName( variable ) ), 0 )

                        result += "    // Unpack from " + variable.getName() + "\n"
                    else:
                        assign_source = Identifier( "_python_var_%s.asObject()" % variable.getName(), 0 )


                    child_variables = variable.getTopLevelVariables()

                    iterator_identifier = TempVariableIdentifier( "arg_tuple_iterator_%d_%d" % ( recursion, var_count ) )
                    lvalue_identifiers = [ TempVariableIdentifier( "arg_tuple_value_%d_%d_%d" % ( recursion, var_count, count+1 ) ) for count in range( len( child_variables )) ]

                    result += self.getUnpackTupleCode(
                        assign_source       = assign_source,
                        iterator_identifier = iterator_identifier,
                        lvalue_identifiers  = lvalue_identifiers,
                        context             = context
                    )

                    for count, child_variable in enumerate( child_variables ):
                        result += self.getAssignmentCode(
                            variable   = child_variable,
                            identifier = lvalue_identifiers[ count ],
                            context    = context
                        )

                        result += "\n"

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

        return function_parameter_decl, function_context_decl, function_context_copy, function_context_free, parameter_parsing_code

    def _getDecoratorsCallCode( self, decorators, context ):
        decorator_decl = [ "PyObject *decorator_%d" % ( count + 1 ) for count in range( len( decorators ) ) ]

        def _getCall( count ):
            return self.getFunctionCallCode(
                context             = context,
                function_identifier = Identifier( "decorator_%d" % count, 0 ),
                argument_tuple      = self.getSequenceCreationCode(
                    sequence_kind       = "tuple",
                    element_identifiers = [ Identifier( "result", 1 ) ],
                    context             = context
                ),
                argument_dictionary = Identifier( "NULL", 0 )
            )


        decorator_calls = [ "result = %s;" % _getCall( count + 1 ).getCode() for count in range( len( decorators ) ) ]

        return decorator_decl, decorator_calls


    def _getGeneratorFunctionCode( self, context, function_name, function_identifier, parameters, closure_variables, user_variables, decorators, function_codes, function_filename, function_doc ):
        function_parameter_decl, function_context_decl, function_context_copy, function_context_free, parameter_parsing_code = self._getParameterParsingCode(
            context                = context,
            function_name          = function_name,
            parameters             = parameters,
        )

        local_var_decl = []
        local_var_naming = []

        for user_variable in user_variables:
            local_var_decl.append( self._getLocalVariableInitCode( context, user_variable, in_context = True ) )
            local_var_naming.append( "_python_context->python_var_%s.setVariableName( %s );" % ( user_variable.getName(), context.getConstantHandle( constant = user_variable.getName() ).getCode() ) )

        for closure_variable in closure_variables:
            function_context_decl.append( self._getLocalVariableInitCode( context, variable = closure_variable, in_context = True, shared = True ) )
            function_context_copy.append( "_python_context->python_closure_%s.shareWith( python_closure_%s );" % ( closure_variable.getName(), closure_variable.getName() ) )

        function_creation_args = self._getFunctionCreationArgs(
            decorators        = decorators,
            parameters        = parameters,
            closure_variables = closure_variables,
            is_generator      = False
        )

        function_decorator_decl, function_decorator_calls = self._getDecoratorsCallCode(
            decorators = decorators,
            context    = context
         )

        function_doc = self.getConstantHandle( context = context, constant = function_doc ).getCode()

        result = CodeTemplates.genfunc_context_body_template % {
            "function_identifier"            : function_identifier,
            "function_common_context_decl"   : "\n    ".join( function_context_decl ),
            "function_instance_context_decl" : "\n    ".join( function_parameter_decl + local_var_decl ),
            "function_context_free"          : "\n    ".join( function_context_free ),
        }

        result += CodeTemplates.genfunc_yielder_template % {
            "function_name"           : function_name,
            "function_identifier"     : function_identifier,
            "function_body"           : "\n    ".join( function_codes ),
            "local_var_naming"        : "\n    ".join( local_var_naming ),
            "module"                  : self.getModuleAccessCode( context = context ).getCode(),
            "name_identifier"         : self.getConstantCode( context = context, constant = function_name ),
            "file_identifier"         : self.getConstantCode( context = context, constant = function_filename ),
            "function_tb_maker"       : self.getTracebackMaker( function_identifier ),
            "function_tb_adder"       : self.getTracebackAdder( function_identifier )
        }

        result += CodeTemplates.genfunc_function_template % {
            "function_name"              : function_name,
            "function_identifier"        : function_identifier,
            "parameter_parsing_code"     : parameter_parsing_code,
            "function_context_copy"      : "\n    ".join( function_context_copy ),
            "module"                     : self.getModuleAccessCode( context = context ).getCode(),
        }


        result += CodeTemplates.make_genfunc_with_context_template % {
            "function_name"              : function_name,
            "function_identifier"        : function_identifier,
            "function_creation_args"     : function_creation_args,
            "function_decorator_calls"   : "\n    ".join( function_decorator_calls ),
            "function_context_copy"      : "\n    ".join( function_context_copy ),
            "function_doc"               : function_doc,
            "module"                     : self.getModuleAccessCode( context = context ).getCode(),
        }

        return result

    def _getFunctionCode( self, context, function_name, function_identifier, parameters, closure_variables, user_variables, decorators, function_codes, function_filename, function_doc ):
        function_parameter_decl, function_context_decl, function_context_copy, function_context_free, parameter_parsing_code = self._getParameterParsingCode(
            context                = context,
            function_name          = function_name,
            parameters             = parameters,
        )

        function_parameter_decl_code = "   \n".join( function_parameter_decl )

        if function_parameter_decl_code:
            parameter_parsing_code = function_parameter_decl_code + parameter_parsing_code

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

        function_decorator_decl, function_decorator_calls = self._getDecoratorsCallCode(
            decorators = decorators,
            context    = context
         )

        function_doc = self.getConstantHandle( context = context, constant = function_doc ).getCode()

        result = ""

        if function_context_decl:
            result += CodeTemplates.function_context_body_template % {
                "function_identifier" : function_identifier,
                "function_context_decl"      : "\n    ".join( function_context_decl ),
                "function_context_free"      : "\n    ".join( function_context_free ),
            }

            context_access_template = CodeTemplates.function_context_access_template % {
                "function_identifier" : function_identifier,
            }
        else:
            context_access_template = CodeTemplates.function_context_unused_template;

        result += CodeTemplates.function_body_template % {
            "function_name"           : function_name,
            "function_identifier"     : function_identifier,
            "context_access_template" : context_access_template,
            "parameter_parsing_code"  : parameter_parsing_code,
            "function_locals"         : "\n    ".join( local_var_inits ),
            "function_body"           : "\n    ".join( function_codes ),
            "module"                  : self.getModuleAccessCode( context = context ).getCode(),
            "name_identifier"         : self.getConstantCode( context = context, constant = function_name ),
            "file_identifier"         : self.getConstantCode( context = context, constant = function_filename ),
            "function_tb_maker"       : self.getTracebackMaker( function_identifier ),
            "function_tb_adder"       : self.getTracebackAdder( function_identifier )
        }

        if function_context_decl:
            result += CodeTemplates.make_function_with_context_template % {
                "function_name"              : function_name,
                "function_identifier"        : function_identifier,
                "function_creation_args"     : function_creation_args,
                "function_decorator_calls"   : "\n    ".join( function_decorator_calls ),
                "function_context_copy"      : "\n    ".join( function_context_copy ),
                "function_doc"               : function_doc,
                "module"                     : self.getModuleAccessCode( context = context ).getCode(),
            }
        else:
            result += CodeTemplates.make_function_without_context_template % {
                "function_name"              : function_name,
                "function_identifier"        : function_identifier,
                "function_creation_args"     : function_creation_args,
                "function_decorator_calls"   : "\n    ".join( function_decorator_calls ),
                "function_doc"               : function_doc,
                "module"                     : self.getModuleAccessCode( context = context ).getCode(),
            }

        return result

    def getGeneratorExpressionCode( self, context, generator, generator_identifier, generator_code, generator_conditions, generator_iterateds, loop_var_codes ):
        function_name     = generator.getFullName()
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
            "function_identifier"        : generator_identifier,
            "function_context_decl"      : "\n    ".join( function_context_decl ),
            "function_context_release"   : "\n    ".join( function_context_release ),
            "iterator_count"             : len( generator.getTargets() )
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
            "module"                     : self.getModuleAccessCode( context = context ).getCode(),
            "name_identifier"            : self.getConstantCode( context = context, constant = function_name ),
            "file_identifier"            : self.getConstantCode( context = context, constant = function_filename ),
        }

        result += CodeTemplates.make_genexpr_with_context_template % {
            "function_name"              : generator.getFullName(),
            "function_identifier"        : generator_identifier,
            "function_creation_args"     : ", ".join( function_creation_args ),
            "function_context_copy"      : "\n    ".join( function_context_copy ),
            "function_doc"               : "Py_None",
            "module"                     : self.getModuleAccessCode( context = context ).getCode(),
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

            kind = "PyObjectSharedLocalVariable" if variable.getReferenced().isShared() else "PyObjectLocalVariable"

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
        class_creation_args.append( "PyObject *bases" );
        class_creation_args.append( "PyObject *dict" );

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

    def getClassCode( self, context, class_def, class_codes, module_name ):
        class_variables = class_def.getClassVariables()

        class_var_decl = []

        def mangleName( name ):
            if not name.startswith( "__" ) or name.endswith( "__" ):
                return name
            else:
                return "_" + class_def.getName() + name

        for class_variable in class_variables:
            class_var_decl.append( "PyObjectLocalVariable _python_var_%s( %s );" % ( class_variable.getName(), context.getConstantHandle( constant = mangleName( class_variable.getName() ) ).getCode() ) )

        class_creation_args, class_dict_args = self._getClassCreationArgs(
            class_def = class_def,
            context   = context
        )

        auto_static = ( "__new__", )
        class_dict_creation = ""

        for class_variable in class_variables:
            class_key = class_variable.getName()

            if class_key in auto_static:
                var_identifier = LocalVariableIdentifier( class_variable.getName() )
                class_dict_creation += '%s = MAKE_STATIC_METHOD( %s );\n' % ( var_identifier.getCode(), var_identifier.getCodeObject() )

        class_dict_creation += "PyObject *result = MAKE_LOCALS_DICT( %s );" % ", ".join( "&%s" % LocalVariableIdentifier( class_variable.getName() ).getCode() for class_variable in class_variables )

        class_decorator_decl, class_decorator_calls = self._getDecoratorsCallCode(
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
            "module_name"           : self.getConstantCode( constant = module_name, context = context ),
            "class_dict_args"       : ", ".join( class_dict_args ),
            "class_creation_args"   : ", ".join( class_creation_args ),
            "class_var_decl"        : "\n    ".join( class_var_decl ),
            "class_dict_creation"   : class_dict_creation,
            "class_decorator_calls" : "\n    ".join( class_decorator_calls ),
            "class_body"            : "\n    ".join( class_codes ),
            "metaclass_global_test" : self.getVariableTestCode(
                context  = context,
                variable = metaclass_variable
            ),
            "metaclass_global_var"  : self.getVariableHandle(
                context  = context,
                variable = metaclass_variable
            ).getCode(),
        }
