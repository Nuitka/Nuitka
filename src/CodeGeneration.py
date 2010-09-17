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
""" The code generation.

No language specifics at all are supposed to be present here. Instead it is using
primitives from the given generator objects to build either Identifiers or to
build code constructs.

As such this is the place that knows how to take a condition and two code branches
and make a code block out of it.
"""

import TreeOperations
import Generator
import Contexts
import Options

def mangleAttributeName( attribute_name, node ):
    if not attribute_name.startswith( "__" ) or attribute_name.endswith( "__" ):
        return attribute_name

    seen_function = False

    while node is not None:
        node = node.getParent()

        if node.isClassReference():
            if seen_function:
                return "_" + node.getName() + attribute_name
            else:
                return attribute_name
        elif node.isFunctionReference():
            seen_function = True

    return attribute_name

def generateSequenceCreationCode( sequence_kind, elements, context, generator ):
    # print "   generateSequenceCreationCode:", sequence_kind, "in", context, "with", generator

    identifiers = generateExpressionsCode(
        expressions = elements,
        context     = context,
        generator   = generator
    )

    return generator.getSequenceCreationCode(
        sequence_kind       = sequence_kind,
        element_identifiers = identifiers,
        context             = context
    )

def generateContractionCode( contraction, context, generator ):
    loop_var_assigns = contraction.getLoopVariableAssignments()
    body             = contraction.getBody()

    loop_var_codes = []

    for count, loop_var_assign in enumerate( loop_var_assigns ):
        loop_var_code = generateAssignmentCode(
            targets   = [ loop_var_assign ],
            value     = generator.getContractionIterValueIdentifier( index = count + 1, context = context ),
            context   = context,
            generator = generator
        )

        loop_var_codes.append( loop_var_code )

    contraction_code = generateExpressionCode(
        context    = context,
        generator  = generator,
        expression = body
    )

    iterateds        = contraction.getIterateds()

    iterated_identifier = generateExpressionCode(
        expression = iterateds[0],
        context    = context.getParent(),
        generator  = generator,
    )

    sub_iterated_identifiers = generateExpressionsCode(
        expressions = iterateds[1:],
        context     = context,
        generator   = generator
    )

    conditions = contraction.getConditions()
    contraction_condition_identifiers = []

    for condition in conditions:
        if condition is None:
            contraction_condition_identifier = generator.getTrueExpressionCode()
        else:
            contraction_condition_identifier = generator.getConditionCheckTrueCode(
                context   = context,
                condition = generateExpressionCode(
                    context    = context,
                    generator  = generator,
                    expression = condition
                )
            )

        contraction_condition_identifiers.append( contraction_condition_identifier )

    contraction_identifier = contraction.getCodeName()

    context.addContractionCodes(
        contraction            = contraction,
        contraction_identifier = contraction_identifier,
        contraction_context    = context,
        contraction_code       = contraction_code,
        loop_var_codes         = loop_var_codes,
        contraction_conditions = contraction_condition_identifiers,
        contraction_iterateds  = sub_iterated_identifiers
    )

    code = generator.getContractionCallCode(
        contraction            = contraction,
        contraction_identifier = contraction_identifier,
        contraction_iterated   = iterated_identifier,
        context                = context.getParent()
    )

    return code

def generateListContractionCode( contraction, context, generator ):
    # Have a separate context to create list contraction code.
    contraction_context = Contexts.PythonListContractionContext(
        parent         = context,
        loop_variables = contraction.getTargetVariables()
    )

    return generateContractionCode(
        contraction = contraction,
        context     = contraction_context,
        generator   = generator
    )

def generateGeneratorExpressionCode( generator_expression, context, generator ):
    # Have a separate context to create generator expression code.
    generator_context = Contexts.PythonGeneratorExpressionContext(
        parent         = context,
        loop_variables = generator_expression.getTargetVariables()
    )

    return generateContractionCode(
        contraction = generator_expression,
        context     = generator_context,
        generator   = generator
    )

def generateGeneratorExpressionBodyCode( generator_expression, context, generator ):
    context = Contexts.PythonGeneratorExpressionContext(
        parent        = context,
        generator_def = generator_expression
    )

    codes = generateExpressionCode(
        expression = generator_expression.getBody(),
        context    = context,
        generator  = generator,
    )

    return context, codes

def generateLambdaCode( lambda_expression, context, generator ):
    assert lambda_expression.isExpressionLambda()

    lambda_context = Contexts.PythonLambdaExpressionContext(
        parent          = context,
        parameter_names = lambda_expression.getParameters().getParameterNames()
    )

    if not lambda_expression.isGenerator():
        code = generator.getReturnCode(
            context    = context,
            identifier = generateExpressionCode(
                expression = lambda_expression.getLambdaExpression(),
                context    = lambda_context,
                generator  = generator,
            )
        )
    else:
        code = generator.getStatementCode(
            identifier = generator.getYieldCode(
                context    = context,
                identifier = generateExpressionCode(
                    expression = lambda_expression.getLambdaExpression().getExpression(),
                    context    = lambda_context,
                    generator  = generator,
                )
            )
        )

    if Options.shallHaveStatementLines():
        codes = [ generator.getCurrentLineCode( lambda_expression.getSourceReference() ), code ]
    else:
        codes = [ code ]

    context.addLambdaCodes(
        lambda_def     = lambda_expression,
        lambda_code    = codes,
        lambda_context = lambda_context
    )

    default_value_identifiers = []

    for _default_parameter_name, default_parameter_value in lambda_expression.getParameters().getDefaultParameters():
        default_value_identifiers.append(
            generateExpressionCode(
                expression = default_parameter_value,
                context    = context,
                generator  = generator
            )
        )

    code = generator.getLambdaExpressionReferenceCode(
        lambda_expression = lambda_expression,
        context           = context,
        default_values    = default_value_identifiers
    )

    return code

class _OverflowCheckVisitor:
    def __init__( self ):
        self.result = False

    def __call__( self, node ):
        if node.isStatementImportFrom():
            for local_name, variable in node.getImports():
                if local_name == "*":
                    raise TreeOperations.ExitVisit

def hasOverflowLocalsNeed( node ):
    visitor = _OverflowCheckVisitor()

    TreeOperations.visitTree( node, visitor )

    return visitor.result

def generateFunctionBodyCode( function, context, generator ):
    body = function.getBody()

    context = Contexts.PythonFunctionContext(
        parent      = context,
        function    = function,
        locals_dict = hasOverflowLocalsNeed( body )
    )

    codes = generateStatementSequenceCode(
        context            = context,
        statement_sequence = body,
        generator          = generator
    )

    return context, codes

def generateFunctionCode( function, context, generator ):
    assert function.isFunctionReference()

    function_context, function_codes = generateFunctionBodyCode(
        function  = function,
        context   = context,
        generator = generator
    )

    context.addFunctionCodes(
        function         = function,
        function_context = function_context,
        function_codes   = function_codes,
    )

    default_value_identifiers = []

    for _default_parameter_name, default_parameter_value in function.getParameters().getDefaultParameters():
        default_value_identifiers.append(
            generateExpressionCode(
                expression = default_parameter_value,
                context    = context,
                generator  = generator
            )
        )

    decorators = generateExpressionsCode(
        expressions = function.getDecorators(),
        context     = context,
        generator   = generator
    )

    function_creation_identifier = generator.getFunctionCreationCode(
        function       = function,
        decorators     = decorators,
        default_values = default_value_identifiers,
        context        = context
    )

    return generator.getAssignmentCode(
        variable   = function.getTargetVariable(),
        identifier = function_creation_identifier,
        context    = context
    )

def generateClassBodyCode( class_def, context, generator ):
    context = Contexts.PythonClassContext(
        parent    = context,
        class_def = class_def
    )

    codes = generateStatementSequenceCode(
        context            = context,
        statement_sequence = class_def.getBody(),
        generator          = generator
    )

    return codes


def generateClassCode( class_def, context, generator ):
    assert class_def.isClassReference()

    bases = []

    for base_class in class_def.getBaseClasses():
        bases.append(
            generateExpressionCode(
                expression = base_class,
                context    = context,
                generator  = generator
            )
        )

    bases_identifier = generator.getSequenceCreationCode(
        sequence_kind       = "tuple",
        element_identifiers = bases,
        context             = context
    )

    class_codes = generateClassBodyCode(
        class_def = class_def,
        context   = context,
        generator = generator
    )

    dict_identifier = generator.getClassDictCreationCode(
        class_def = class_def,
        context   = context
    )

    decorators = generateExpressionsCode(
        expressions = class_def.getDecorators(),
        context     = context,
        generator   = generator
    )

    class_creation_identifier = generator.getClassCreationCode(
        code_name        = class_def.getCodeName(),
        bases_identifier = bases_identifier,
        dict_identifier  = dict_identifier,
        decorators       = decorators,
        context          = context
    )

    context.addClassCodes(
        class_def   = class_def,
        class_codes = class_codes,
    )

    return generator.getAssignmentCode(
        variable   = class_def.getTargetVariable(),
        identifier = class_creation_identifier,
        context    = context
    )


def generateOperationCode( operator, operands, context, generator ):
    operand_identifiers = []

    for operand in operands:
        identifier = generateExpressionCode(
            expression = operand,
            context    = context,
            generator  = generator
        )

        operand_identifiers.append( identifier )

    return generator.getOperationCode( context, operator, operand_identifiers )


def generateComparisonExpressionCode( comparison_expression, context, generator ):
    return generator.getComparisonExpressionCode(
        comparators = comparison_expression.getComparators(),
        operands    = [ generateExpressionCode( expression = operand, context = context, generator = generator ) for operand in comparison_expression.getOperands() ],
        context     = context
    )

def generateDictionaryCreationCode( keys, values, context, generator ):
    key_identifiers = []

    for key in keys:
        identifier = generateExpressionCode(
            expression = key,
            context    = context,
            generator  = generator
        )

        key_identifiers.append( identifier )

    value_identifiers = []

    for value in values:
        identifier = generateExpressionCode(
            expression = value,
            context    = context,
            generator  = generator
        )

        value_identifiers.append( identifier )

    return generator.getDictionaryCreationCode(
        keys    = key_identifiers,
        values  = value_identifiers,
        context = context
    )

def _areConstants( expressions ):
    for expression in expressions:
        if not expression.isConstantReference():
            return False
    else:
        return True

def generateSliceRangeIdentifier( lower, upper, context, generator ):
    if lower is None:
        lower = generator.getMinIndexCode( context = context )
    else:
        lower = generator.getIndexCode(
            context    = context,
            identifier = generateExpressionCode(
                expression = lower,
                context    = context,
                generator  = generator
            )
        )

    if upper is None:
        upper = generator.getMaxIndexCode( context = context )
    else:
        upper = generator.getIndexCode(
            context    = context,
            identifier = generateExpressionCode(
                expression = upper,
                context    = context,
                generator  = generator
            )
        )

    return lower, upper

def generateSliceAccessIdentifiers( sliced, lower, upper, context, generator ):
    lower, upper = generateSliceRangeIdentifier( lower, upper, context, generator )

    sliced = generateExpressionCode(
        expression = sliced,
        context    = context,
        generator  = generator
    )

    return sliced, lower, upper


def generateExpressionsCode( expressions, context, generator ):
    assert type( expressions ) in ( tuple, list )

    return [ generateExpressionCode( expression = expression, context = context, generator = generator ) for expression in expressions ]

def generateExpressionCode( expression, context, generator ):
    # print "*" * 80
    # print "  generateExpressionCode:", expression, "in", context, "with", generator

    def makeExpressionCode( expression, allow_none = False ):
        if allow_none and expression is None:
            return None

        return generateExpressionCode(
            expression = expression,
            context    = context,
            generator  = generator
        )

    if not expression.isExpression():
        print "No expression", expression
        print expression.dump()
        print expression.parent
        assert False

    # print "Expression ->", expression, type( expression ) if type( expression ) != type( context ) else expression.__class__

    if expression.isVariableReference():
        if expression.getVariable() is None:
            print expression.getVariableName(), expression.getSourceReference()
            expression.dump()
            assert False

        identifier = generator.getVariableHandle(
            variable = expression.getVariable(),
            context  = context
        )
    elif expression.isConstantReference():
        identifier = generator.getConstantHandle(
            constant   = expression.getConstant(),
            context    = context
        )
    elif expression.isOperation():
        identifier = generateOperationCode(
            operator  = expression.getOperation(),
            operands  = expression.getOperands(),
            context   = context,
            generator = generator
        )
    elif expression.isSequenceCreation():
        identifier = generateSequenceCreationCode(
            sequence_kind = expression.getSequenceKind(),
            elements      = expression.getElements(),
            context       = context,
            generator     = generator
        )
    elif expression.isDictionaryCreation():
        identifier = generateDictionaryCreationCode(
            keys      = expression.getKeys(),
            values    = expression.getValues(),
            context   = context,
            generator = generator
        )
    elif expression.isFunctionCall():
        function_identifier = generateExpressionCode(
            expression = expression.getCalledExpression(),
            context    = context,
            generator  = generator
        )

        positional_args = expression.getPositionalArguments()
        star_list_arg = expression.getStarListArg()

        if _areConstants( positional_args ) and star_list_arg is None:
            args_identifier = generator.getConstantHandle(
                context = context,
                constant = tuple( ( positional_arg.getConstant() for positional_arg in positional_args ) )
            )

            args_tuple = True
        else:
            if positional_args:
                positional_args_identifier = generateSequenceCreationCode(
                    sequence_kind = "tuple",
                    elements      = positional_args,
                    context       = context,
                    generator     = generator
                )
            else:
                positional_args_identifier = None

            if star_list_arg is not None:
                star_arg_identifier = generateExpressionCode(
                    expression = star_list_arg,
                    context    = context,
                    generator  = generator
                )
            else:
                star_arg_identifier = None

            if positional_args_identifier is not None and star_arg_identifier is not None:
                args_identifier = generator.getSequenceConcatCode(
                    seq1_identifier = positional_args_identifier,
                    seq2_identifier = generator.getTupleConversionCode(
                        sequence_identifier = star_arg_identifier
                    )
                )

                args_tuple = False
            elif positional_args_identifier is None and star_arg_identifier is not None:
                args_identifier = star_arg_identifier

                args_tuple = False
            elif positional_args_identifier is not None and star_arg_identifier is None:
                args_identifier = positional_args_identifier

                args_tuple = True
            else:
                assert False

        if not args_tuple:
            args_identifier = generator.getTupleConversionCode( sequence_identifier = args_identifier )

        named_arguments = expression.getNamedArguments()
        star_dict_arg = expression.getStarDictArg()

        if _areConstants( [ value for (_name, value) in named_arguments ] ):
            named_arg_dict = {}

            for named_arg_desc in named_arguments:
                named_arg_name, named_arg_value = named_arg_desc

                named_arg_dict[ named_arg_name ] = named_arg_value.getConstant()

            kw_identifier = generator.getConstantHandle( context = context, constant = named_arg_dict )
        else:
            kw_key_identifiers = []
            kw_value_identifiers = []

            for named_arg_desc in named_arguments:
                named_arg_name, named_arg_value = named_arg_desc
                assert type( named_arg_name ) == str

                named_arg_value_identifier = generateExpressionCode(
                    expression = named_arg_value,
                    context    = context,
                    generator  = generator
                )

                kw_key_identifiers.append( generator.getConstantHandle( context = context, constant = named_arg_name ) )
                kw_value_identifiers.append( named_arg_value_identifier )

            kw_identifier = generator.getDictionaryCreationCode(
                context = context,
                keys    = kw_key_identifiers,
                values  = kw_value_identifiers
            )

        if star_dict_arg is not None:
            star_dict_identifier = generateExpressionCode(
                expression = star_dict_arg,
                context    = context,
                generator  = generator
            )

            if kw_identifier.getCode() == "_python_dict_empty":
                kw_identifier = star_dict_identifier
            else:
                kw_identifier = generator.getDictionaryMergeCode(
                   dict1_identifier = kw_identifier,
                   dict2_identifier = star_dict_identifier
                )

        identifier = generator.getFunctionCallCode(
            function_identifier = function_identifier,
            argument_tuple      = args_identifier,
            argument_dictionary = kw_identifier,
            context             = context,
        )
    elif expression.isListContraction():
        identifier = generateListContractionCode(
            contraction = expression,
            context     = context,
            generator   = generator
        )
    elif expression.isAttributeLookup():
        attribute_name = mangleAttributeName(
            attribute_name = expression.getAttributeName(),
            node           = expression
        )

        identifier = generator.getAttributeLookupCode(
            context        = context,
            attribute_name = attribute_name,
            source         = makeExpressionCode( expression.getLookupSource() ),
        )
    elif expression.isSubscriptLookup():
        identifier = generator.getSubscriptLookupCode(
            context   = context,
            subscript = generateExpressionCode(
                expression = expression.getSubscript(),
                generator  = generator,
                context    = context
            ),
            source    = generateExpressionCode(
                expression = expression.getLookupSource(),
                context    = context,
                generator  = generator
            )
        )
    elif expression.isSliceLookup():
        expression_identifier, lower_identifier, upper_identifier = generateSliceAccessIdentifiers(
            sliced    = expression.getLookupSource(),
            lower     = expression.getLower(),
            upper     = expression.getUpper(),
            context   = context,
            generator = generator
        )

        identifier = generator.getSliceLookupCode(
            source  = expression_identifier,
            lower   = lower_identifier,
            upper   = upper_identifier,
            context = context
        )

    elif expression.isSliceObjectExpression():
        identifier = generator.getSliceObjectCode(
            lower = makeExpressionCode(
                expression = expression.getLower(),
                allow_none = True
            ),
            upper = makeExpressionCode(
                expression = expression.getUpper(),
                allow_none = True
            ),
            step  = makeExpressionCode(
                expression = expression.getStep(),
                allow_none = True
            ),
            context = context
        )
    elif expression.isConditionOR():
        expression_identifiers = generateExpressionsCode( expressions = expression.getExpressions(), generator = generator, context = context )

        identifier = generator.getSelectionOrCode(
            conditions = expression_identifiers,
            context    = context
        )

    elif expression.isConditionAND():
        expression_identifiers = generateExpressionsCode( expressions = expression.getExpressions(), generator = generator, context = context )

        identifier = generator.getSelectionAndCode(
            conditions = expression_identifiers,
            context    = context
        )
    elif expression.isConditionNOT():
        identifier = generator.getConditionNotCode(
            condition = generateExpressionCode( expression = expression.getExpression(), generator = generator, context = context ),
            context   = context
        )
    elif expression.isConditionalExpression():
        identifier = generator.getConditionalExpressionCallCode(
            condition = makeExpressionCode( expression.getCondition() ),
            codes_yes = makeExpressionCode( expression.getExpressionYes() ),
            codes_no  = makeExpressionCode( expression.getExpressionNo() ),
            context   = context
        )
    elif expression.isBuiltinGlobals():
        identifier = generator.getLoadGlobalsCode(
            context = context,
            module  = expression.getParentModule()
        )
    elif expression.isBuiltinLocals():
        identifier = generator.getLoadLocalsCode(
            context  = context,
            provider = expression.getParentVariableProvider()
        )
    elif expression.isBuiltinDir():
        identifier = generator.getLoadDirCode(
            context  = context,
            provider = expression.getParentVariableProvider()
        )
    elif expression.isBuiltinVars():
        identifier = generator.getLoadVarsCode(
            context    = context,
            identifier = makeExpressionCode( expression.getSource() )
        )
    elif expression.isBuiltinEval():
        identifier = generateEvalCode(
            generator       = generator,
            context         = context,
            eval_expression = expression
        )
    elif expression.isBuiltinOpen():
        identifier = generator.getBuiltinOpenCode(
            filename  = makeExpressionCode(
                expression = expression.getFilename(),
                allow_none = True
            ),
            mode      = makeExpressionCode(
                expression = expression.getMode(),
                allow_none = True
            ),
            buffering = makeExpressionCode(
                expression = expression.getBuffering(),
                allow_none = True
            ),
            context   = context
        )
    elif expression.isExpressionLambda():
        identifier = generateLambdaCode(
            lambda_expression = expression,
            context           = context,
            generator         = generator
        )
    elif expression.isExpressionGenerator():
        identifier = generateGeneratorExpressionCode(
            generator_expression = expression,
            context              = context,
            generator            = generator
        )
    elif expression.isExpressionComparison():
        identifier = generateComparisonExpressionCode(
            comparison_expression = expression,
            context               = context,
            generator             = generator
        )
    elif expression.isExpressionYield():
        yielded = expression.getExpression()

        if yielded is not None:
            identifier = generator.getYieldCode(
                identifier = makeExpressionCode( yielded ),
                context    = context
            )
        else:
            identifier = generator.getYieldCode(
                identifier = generator.getConstantHandle( constant = None, context = context ),
                context    = context
            )

    else:
        assert False, expression

    if not hasattr( identifier, "getCode" ):
        assert False, identifier

    return identifier


def generateAssignmentCode( targets, value, context, generator, recursion = 1 ):
    if len( targets ) == 1 and not targets[0].isAssignToTuple():
        assign_source = value
        code = ""

        brace = False
    else:
        if value.getRefCount():
            code = "PyObjectTemporary _python_rvalue_%d( %s );\n" % ( recursion, value.getCodeObject() )
            assign_source = Generator.Identifier( "_python_rvalue_%d.asObject()" % recursion, 0 )
        else:
            code = "PyObject *_python_rvalue_%d = %s;\n" % ( recursion, value.getCodeObject() )
            assign_source = Generator.Identifier( "_python_rvalue_%d" % recursion, 0 )

        brace = True

    old_ref_count = value.getRefCount()

    for target in targets:
        if target.isAssignToSubscript():
            code += generator.getSubscriptAssignmentCode(
                subscribed    = generateExpressionCode(
                    expression = target.getSubscribed(),
                    generator  = generator,
                    context    = context
                ),
                subscript     = generateExpressionCode(
                    expression = target.getSubscript(),
                    generator  = generator,
                    context    = context
                ),
                identifier    = assign_source,
                context       = context
            )

            if old_ref_count:
                value.setRefCount( 0 )
        elif target.isAssignToAttribute():
            attribute_name = mangleAttributeName(
                attribute_name = target.getAttributeName(),
                node           = target
            )

            code += generator.getAttributeAssignmentCode(
                target         = generateExpressionCode(
                    expression = target.getLookupSource(),
                    generator  = generator,
                    context    = context
                ),
                attribute_name = attribute_name,
                identifier     = assign_source,
                context        = context
            )

            if old_ref_count:
                value.setRefCount( 0 )
        elif target.isAssignToSlice():
            expression_identifier, lower_identifier, upper_identifier = generateSliceAccessIdentifiers(
                sliced    = target.getLookupSource(),
                lower     = target.getLower(),
                upper     = target.getUpper(),
                context   = context,
                generator = generator
            )

            code += generator.getSliceAssignmentCode(
                target     = expression_identifier,
                upper      = upper_identifier,
                lower      = lower_identifier,
                identifier = assign_source,
                context    = context
            )
        elif target.isAssignToVariable():
            code += generator.getAssignmentCode(
                variable   = target.getTargetVariable(),
                identifier = assign_source,
                context    = context
            )

            if old_ref_count:
                value.setRefCount( 0 )
        elif target.isAssignToTuple():
            elements = target.getElements()

            iterator_identifier = generator.getTupleUnpackIteratorCode( recursion )

            lvalue_identifiers = [ generator.getTupleUnpackLeftValueCode( recursion, count+1 ) for count in range( len( elements )) ]

            code += generator.getUnpackTupleCode(
                assign_source       = assign_source,
                iterator_identifier = iterator_identifier,
                lvalue_identifiers  = lvalue_identifiers,
                context             = context
            )

            for count, element in enumerate( elements ):
                code += generateAssignmentCode(
                    targets   = [ element ],
                    value     = lvalue_identifiers[ count ],
                    generator = generator,
                    context   = context,
                    recursion = recursion + 1
                )

        else:
            assert False, (target, target.getSourceReference())

        code += "\n"

    assert code.endswith( "\n" )

    if recursion == 1:
        code = "\n".join( [ "   " + line for line in code.split( "\n" ) ] )

    if brace:
        code = "{\n%s\n}" % code

    if old_ref_count:
        value.setRefCount( old_ref_count )

    return code

def generateDelCode( targets, context, generator ):
    code = ""

    def makeExpressionCode( expression, allow_none = False ):
        if allow_none and expression is None:
            return None

        return generateExpressionCode(
            expression = expression,
            context    = context,
            generator  = generator
        )

    for target in targets:
        if target.isAssignToSubscript():
            code += generator.getSubscriptDelCode(
                subscribed = makeExpressionCode( target.getSubscribed() ),
                subscript  = makeExpressionCode( target.getSubscript() ),
                context    = context
            )
        elif target.isAssignToAttribute():
            attribute_name = mangleAttributeName(
                attribute_name = target.getAttributeName(),
                node           = target
            )

            code += generator.getAttributeDelCode(
                target         = makeExpressionCode( target.getLookupSource() ),
                attribute_name = attribute_name,
                context        = context
            )
        elif target.isAssignToVariable():
            code += generator.getVariableDelCode(
                variable = target.getTargetVariable(),
                context  = context
            )
        elif target.isAssignToTuple():
            elements = target.getElements()

            for element in elements:
                code += generateDelCode(
                    targets   = [ element ],
                    generator = generator,
                    context   = context
                )

        elif target.isAssignToSlice():
            code += generator.getSliceDelCode(
                target     = makeExpressionCode( target.getLookupSource() ),
                upper      = makeExpressionCode( target.getUpper(), allow_none = True ),
                lower      = makeExpressionCode( target.getLower(), allow_none = True ),
                context    = context
            )
        else:
            assert False, target

    return code

def generateEvalCode( eval_expression, context, generator ):
    exec_globals = eval_expression.getGlobals()

    if exec_globals is None:
        globals_identifier = generator.getConstantHandle( constant = None, context = context )
    else:
        globals_identifier = generateExpressionCode(
            expression = exec_globals,
            context    = context,
            generator  = generator
        )

    exec_locals = eval_expression.getLocals()

    if exec_locals is None:
        locals_identifier = generator.getConstantHandle( constant = None, context = context )
    else:
        locals_identifier = generateExpressionCode(
            expression = exec_locals,
            context    = context,
            generator  = generator
        )

    identifier = generator.getEvalCode(
        exec_code          = generateExpressionCode(
            generator    = generator,
            context      = context,
            expression   = eval_expression.getSource(),
        ),
        globals_identifier = globals_identifier,
        locals_identifier  = locals_identifier,
        mode               = eval_expression.getMode(),
        future_flags       = generator.getFutureFlagsCode( *eval_expression.getFutureFlags() ),
        provider           = eval_expression.getParentVariableProvider(),
        context            = context

    )

    return identifier

def generateExecCode( exec_def, context, generator ):
    exec_globals = exec_def.getGlobals()

    if exec_globals is None:
        globals_identifier = generator.getConstantHandle( constant = None, context = context )
    else:
        globals_identifier = generateExpressionCode(
            expression = exec_globals,
            context    = context,
            generator  = generator
        )

    exec_locals = exec_def.getLocals()

    if exec_locals is None:
        locals_identifier = generator.getConstantHandle( constant = None, context = context )
    elif exec_locals is not None:
        locals_identifier = generateExpressionCode(
            expression = exec_locals,
            context    = context,
            generator  = generator
        )

    return generator.getExecCode(
        context            = context,
        provider           = exec_def.getParentVariableProvider(),
        exec_code          = generateExpressionCode(
            generator  = generator,
            context    = context,
            expression = exec_def.getSource()
        ),
        globals_identifier = globals_identifier,
        locals_identifier  = locals_identifier,
        future_flags       = generator.getFutureFlagsCode( *exec_def.getFutureFlags() )
    )

def generateStatementCode( statement, context, generator ):
    try:
        return _generateStatementCode( statement, context, generator )
    except:
        print "Problem with", statement, "at", statement.getSourceReference()
        raise

def _generateStatementCode( statement, context, generator ):
    if not statement.isStatement():

        # A statement sequence may turn up due to
        if statement.isStatementsSequence() and statement.isReplacedStatement():
            codes = generateStatementSequenceCode(
                statement_sequence = statement,
                generator          = generator,
                context            = context
            )

            return "\n   ".join( codes )

        print statement.dump()
        assert False


    def makeExpressionCode( expression, allow_none = False ):
        if allow_none and expression is None:
            return None

        return generateExpressionCode(
            expression = expression,
            context     = context,
            generator   = generator
        )

    if statement.isStatementAssignment():
        source = statement.getSource()

        if source is not None:
            code = generateAssignmentCode(
                targets   = statement.getTargets(),
                value     = makeExpressionCode( source ),
                context   = context,
                generator = generator
            )
        else:
            code = generateDelCode(
                targets   = statement.getTargets(),
                context   = context,
                generator = generator
            )
    elif statement.isStatementInplaceAssignment():
        target = statement.getTarget()

        if target.isAssignToVariable():
            code = generator.getInplaceVarAssignmentCode(
                variable   = target.getTargetVariable(),
                operator   = statement.getOperator(),
                identifier = makeExpressionCode( statement.getExpression() ),
                context    = context
            )
        elif target.isAssignToSubscript():
            code = generator.getInplaceSubscriptAssignmentCode(
                subscribed = makeExpressionCode(
                    expression = target.getSubscribed()
                ),
                subscript  = makeExpressionCode(
                    expression = target.getSubscript()
                ),
                operator   = statement.getOperator(),
                identifier = makeExpressionCode( statement.getExpression() ),
                context    = context
            )
        elif target.isAssignToAttribute():
            attribute_name = mangleAttributeName(
                attribute_name = target.getAttributeName(),
                node           = target
            )

            code = generator.getInplaceAttributeAssignmentCode(
                target          = makeExpressionCode(
                    expression = target.getLookupSource()
                ),
                attribute_name  = attribute_name,
                operator        = statement.getOperator(),
                identifier      = makeExpressionCode( statement.getExpression() ),
                context         = context
            )
        elif target.isAssignToSlice():
            target_identifier, lower_identifier, upper_identifier = generateSliceAccessIdentifiers(
                sliced    = target.getLookupSource(),
                lower     = target.getLower(),
                upper     = target.getUpper(),
                context   = context,
                generator = generator
            )

            code = generator.getInplaceSliceAssignmentCode(
                target     = target_identifier,
                lower      = lower_identifier,
                upper      = upper_identifier,
                operator   = statement.getOperator(),
                identifier = makeExpressionCode( statement.getExpression() ),
                context    = context
            )
        else:
            assert False, ( "not supported for inplace assignment", target, target.getSourceReference() )
    elif statement.isFunctionReference():
        code = generateFunctionCode(
            function  = statement,
            context   = context,
            generator = generator
        )
    elif statement.isStatementExpression():
        code = generator.getStatementCode(
            identifier = makeExpressionCode( statement.getExpression() )
        )
    elif statement.isStatementPrint():
        if statement.getDestination() is not None:
            target_file = makeExpressionCode( statement.getDestination() )
        else:
            target_file = None

        values = generateExpressionsCode(
            generator   = generator,
            context     = context,
            expressions = statement.getValues()
        )

        code = generator.getPrintCode(
            target_file = target_file,
            identifiers = values,
            newline     = statement.isNewlinePrint(),
            context     = context
        )
    elif statement.isStatementReturn():
        parent_function = statement.getParentFunction()

        if parent_function is not None and parent_function.isGenerator():
            code = generator.getYieldTerminatorCode()
        else:
            expression = statement.getExpression()

            if expression is not None:
                code = generator.getReturnCode(
                    identifier = makeExpressionCode( expression ),
                    context    = context
                )
            else:
                code = generator.getReturnCode(
                    identifier = generator.getConstantHandle( constant = None, context = context ),
                    context    = context
                )
    elif statement.isStatementWith():
        body_codes = generateStatementSequenceCode(
            statement_sequence = statement.getWithBody(),
            generator          = generator,
            context            = context
        )

        with_manager_identifier, with_value_identifier = generator.getWithNames( context = context )

        if statement.getTarget() is not None:
            assign_codes = generateAssignmentCode(
                targets    = [ statement.getTarget() ],
                value      = with_value_identifier,
                context    = context,
                generator  = generator
            )
        else:
            assign_codes = None

        code = generator.getWithCode(
            source_identifier       = makeExpressionCode( statement.getExpression() ),
            assign_codes            = assign_codes,
            with_manager_identifier = with_manager_identifier,
            with_value_identifier   = with_value_identifier,
            body_codes              = body_codes,
            context                 = context
        )

    elif statement.isStatementForLoop():
        iter_name, iter_value = generator.getForLoopNames( context = context )

        iterator = generator.getIteratorCreationCode(
            iterated = makeExpressionCode( statement.getIterated() ),
            context  = context
        )

        assignment_code = generateAssignmentCode(
            targets   = [ statement.getLoopVariableAssignment() ],
            value     = iter_value,
            context   = context,
            generator = generator
        )

        loop_body_codes = generateStatementSequenceCode(
            statement_sequence = statement.getBody(),
            generator          = generator,
            context            = context
        )

        if statement.getNoBreak() is not None:
            loop_else_codes = generateStatementSequenceCode(
                statement_sequence = statement.getNoBreak(),
                generator          = generator,
                context            = context
            )
        else:
            loop_else_codes = []

        line_number_code = generator.getCurrentLineCode( statement.getIterated().getSourceReference() ) if Options.shallHaveStatementLines() else ""

        code = generator.getForLoopCode(
            line_number_code = line_number_code,
            iterator         = iterator,
            iter_name        = iter_name,
            iter_value       = iter_value,
            loop_var_code    = assignment_code,
            loop_body_codes  = loop_body_codes,
            loop_else_codes  = loop_else_codes,
            context          = context
        )
    elif statement.isStatementWhileLoop():
        loop_body_codes = generateStatementSequenceCode(
            statement_sequence = statement.getLoopBody(),
            generator          = generator,
            context            = context
        )

        if statement.getNoEnter() is not None:
            loop_else_codes = generateStatementSequenceCode(
                statement_sequence = statement.getNoEnter(),
                generator          = generator,
                context            = context
            )
        else:
            loop_else_codes = []

        code = generator.getWhileLoopCode(
            condition       = makeExpressionCode( statement.getCondition() ),
            loop_body_codes = loop_body_codes,
            loop_else_codes = loop_else_codes,
            context         = context
        )
    elif statement.isStatementConditional():
        branches_codes = []

        for branch in statement.getBranches():
            branch_codes = generateStatementSequenceCode(
                statement_sequence = branch,
                generator          = generator,
                context            = context
            )

            branches_codes.append( branch_codes )

        code = generator.getBranchCode(
            conditions     = [ makeExpressionCode( condition ) for condition in statement.getConditions() ],
            branches_codes = branches_codes,
            context        = context
        )
    elif statement.isStatementContinue():
        code = generator.getLoopContinueCode()
    elif statement.isStatementBreak():
        code = generator.getLoopBreakCode()
    elif statement.isStatementImportModule():
        code = generator.getImportModulesCode(
            context      = context,
            import_specs = statement.getImports()
        )
    elif statement.isStatementImportFrom():
        code = generator.getImportFromCode(
            module_name = statement.getModuleName(),
            imports     = statement.getImports(),
            context     = context,
        )
    elif statement.isStatementTryFinally():
        code = generator.getTryFinallyCode(
            context     = context,
            code_tried = generateStatementSequenceCode(
                context            = context,
                generator          = generator,
                statement_sequence = statement.getBlockTry()
            ),
            code_final = generateStatementSequenceCode(
                context            = context,
                generator          = generator,
                statement_sequence = statement.getBlockFinal()
            )
        )
    elif statement.isStatementTryExcept():
        exception_identifiers = []

        for catcher in statement.getExceptionCatchers():
            if catcher is not None:
                exception_identifiers.append(
                    makeExpressionCode(
                        expression = catcher
                    )
                )
            else:
                exception_identifiers.append( None )

        exception_assignments = []

        for assign in statement.getExceptionAssigns():
            if assign is not None:
                exception_assignments.append(
                    generateAssignmentCode(
                        targets   = [ assign ],
                        value     = generator.getCurrentExceptionObjectCode(),
                        context   = context,
                        generator = generator
                    )
                )
            else:
                exception_assignments.append( None )

        catcher_codes = []

        for catched in statement.getExceptionCatchBranches():
            catcher_codes.append(
                generateStatementSequenceCode(
                    generator          = generator,
                    context            = context,
                    statement_sequence = catched
                )
            )

        no_raise = statement.getBlockNoRaise()

        if no_raise is not None:
            else_code = generateStatementSequenceCode(
                generator          = generator,
                context            = context,
                statement_sequence = no_raise
            )
        else:
            else_code = None

        code = generator.getTryExceptCode(
            context               = context,
            code_tried            = generateStatementSequenceCode(
                generator          = generator,
                context            = context,
                statement_sequence = statement.getBlockTry()
            ),
            exception_identifiers = exception_identifiers,
            exception_assignments = exception_assignments,
            catcher_codes         = catcher_codes,
            else_code             = else_code
        )
    elif statement.isStatementRaiseException():
        parameters = statement.getExceptionParameters()

        if len( parameters ) == 0:
            code = generator.getReRaiseExceptionCode(
                context = context
            )
        elif len( parameters ) == 1:
            code = generator.getRaiseExceptionCode(
                context                    = context,
                exception_type_identifier  = makeExpressionCode(
                    expression = parameters[0]
                ),
                exception_value_identifier = None,
                exception_tb_identifier    = None,
                exception_tb_maker         = generator.getTracebackMakerCall( context.getCodeName(), statement.getSourceReference().getLineNumber() )
            )
        elif len( parameters ) == 2:
            code = generator.getRaiseExceptionCode(
                context              = context,
                exception_type_identifier = makeExpressionCode(
                    expression = parameters[0]
                ),
                exception_value_identifier = makeExpressionCode(
                    expression = parameters[1]
                ),
                exception_tb_identifier    = None,
                exception_tb_maker         = generator.getTracebackMakerCall( context.getCodeName(), statement.getSourceReference().getLineNumber() )
            )
        elif len( parameters ) == 3:
            code = generator.getRaiseExceptionCode(
                context                    = context,
                exception_type_identifier  = makeExpressionCode(
                    expression = parameters[0]
                ),
                exception_value_identifier = makeExpressionCode(
                    expression = parameters[1]
                ),
                exception_tb_identifier    = makeExpressionCode(
                    expression = parameters[2]
                ),
                exception_tb_maker         = None
            )
        else:
            print parameters

            assert False
    elif statement.isStatementAssert():
        return generator.getAssertCode(
            context              = context,
            condition_identifier = makeExpressionCode( statement.getExpression() ),
            failure_identifier   = makeExpressionCode( statement.getArgument(), allow_none = True ),
            exception_tb_maker   = generator.getTracebackMakerCall( context.getCodeName(), statement.getSourceReference().getLineNumber() )
        )
    elif statement.isStatementExec():
        code = generateExecCode(
            exec_def     = statement,
            generator    = generator,
            context      = context
        )
    elif statement.isStatementDeclareGlobal():
        return ""
    elif statement.isStatementPass():
        return ""
    elif statement.isClassReference():
        code = generateClassCode(
            class_def = statement,
            generator = generator,
            context   = context
        )
    else:
        assert False, statement.__class__

    if Options.shallHaveStatementLines():
        code = generator.getCurrentLineCode( statement.getSourceReference() ) + code

    return code

def generateStatementSequenceCode( statement_sequence, context, generator ):
    # print statement_sequence, "in", context, "with", generator, statement_sequence.parent

    assert statement_sequence.isStatementsSequence(), statement_sequence

    statements = statement_sequence.getStatements()

    codes = []

    for statement in statements:
        if Options.shallTraceExecution():
            codes.append( 'puts( "Execute: %s %s" );' % ( statement.getSourceReference(), statement ) )

        code = generateStatementCode(
            statement = statement,
            context   = context,
            generator = generator
        )

        codes.append( code )

    return codes

def generatePackageCode( package_name, generator ):
    return generator.getPackageCode(
        package_name = package_name
    )

def generateModuleCode( module, module_name, global_context, stand_alone, generator ):
    assert module.isModule()

    context = Contexts.PythonModuleContext(
        module_name    = module_name,
        code_name      = generator.getModuleIdentifier( module_name ),
        global_context = global_context,
    )

    statement_sequence = module.getStatementSequence()

    codes = generateStatementSequenceCode(
        context            = context,
        statement_sequence = statement_sequence,
        generator          = generator
    )

    return generator.getModuleCode(
        module_name         = module_name,
        stand_alone         = stand_alone,
        doc_identifier      = context.getConstantHandle( constant = module.getDoc() ),
        filename_identifier = context.getConstantHandle( constant = module.getFilename() ),
        codes               = codes,
        context             = context,
    )

def generateExecutableCode( main_module, other_modules, generator ):
    assert main_module.isModule()

    global_context = Contexts.PythonGlobalContext()

    # Create code for the other modules.
    other_modules_code = ""

    def myCompare( a, b ):
        return cmp( a.getName(), b.getName() )

    packages_done = set()

    for other_module in sorted( other_modules, cmp = myCompare ):
        package_name = other_module.getPackage()

        if package_name is not None and package_name not in packages_done:
            package_code = generatePackageCode(
                generator    = generator,
                package_name = package_name
            )

            other_modules_code += package_code

            packages_done.add( package_name )

    for other_module in sorted( other_modules, cmp = myCompare ):
        other_module_code = generateModuleCode(
            generator      = generator,
            module         = other_module,
            module_name    = other_module.getFullName(),
            global_context = global_context,
            stand_alone    = False
        )

        other_modules_code += other_module_code

    # Create code for the main module.
    main_module_code = generateModuleCode(
        generator      = generator,
        module         = main_module,
        module_name    = "__main__",
        global_context = global_context,
        stand_alone    = True
    )

    codes = main_module_code + other_modules_code

    return generator.getMainCode(
        codes         = codes,
        other_modules = other_modules
    )
