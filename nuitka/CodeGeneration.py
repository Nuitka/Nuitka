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
""" The code generation.

No language specifics at all are supposed to be present here. Instead it is using
primitives from the given generator to build either Identifiers (referenced counted
expressions) or code sequences (list of strings).

As such this is the place that knows how to take a condition and two code branches and
make a code block out of it. But it doesn't contain any target language syntax.
"""

from __future__ import print_function

from . import (
    Generator,
    Contexts,
    Options,
    Nodes,
    Utils
)

def mangleAttributeName( attribute_name, node ):
    if not attribute_name.startswith( "__" ) or attribute_name.endswith( "__" ):
        return attribute_name

    seen_function = False

    while node is not None:
        node = node.getParent()

        if node is None:
            break

        if node.isClassBody():
            if seen_function:
                return "_" + node.getName() + attribute_name
            else:
                return attribute_name
        elif node.isFunctionBody():
            seen_function = True

    return attribute_name

def generateSequenceCreationCode( sequence_kind, elements, context ):
    if _areConstants( elements ):
        sequence_type = tuple if sequence_kind == "tuple" else list

        return Generator.getConstantHandle(
            context  = context,
            constant = sequence_type( element.getConstant() for element in elements )
        )
    else:
        identifiers = generateExpressionsCode(
            expressions = elements,
            context     = context
        )

        return Generator.getSequenceCreationCode(
            sequence_kind       = sequence_kind,
            element_identifiers = identifiers
        )

def generateConditionCode( condition, context, inverted = False, allow_none = False ):
    if condition is None and allow_none:
        assert not inverted

        return Generator.getTrueExpressionCode()
    elif condition.isConstantReference():
        value = condition.getConstant()

        if inverted:
            value = not value

        if value:
            return Generator.getTrueExpressionCode()
        else:
            return Generator.getFalseExpressionCode()
    elif condition.isExpressionComparison():
        result = Generator.getComparisonExpressionBoolCode(
            comparators = condition.getComparators(),
            operands    = generateExpressionsCode(
                expressions = condition.getOperands(),
                context     = context
            ),
            context     = context
        )

        if inverted:
            result = Generator.getConditionNotBoolCode(
                condition = result
            )

        return result
    else:
        condition_identifier = generateExpressionCode(
            context    = context,
            expression = condition
        )

        if inverted:
            return Generator.getConditionCheckFalseCode(
                condition = condition_identifier
            )
        else:
            return Generator.getConditionCheckTrueCode(
                condition = condition_identifier
            )

def _generatorContractionBodyCode( contraction, context ):
    contraction_body = contraction.getBody()

    # Dictionary contractions produce a tuple always.
    if contraction.isDictContractionBody():
        return (
            generateExpressionCode(
                context    = context,
                expression = contraction_body.getKey()
            ),
            generateExpressionCode(
                context    = context,
                expression = contraction_body.getValue()
            )
        )
    else:
        return generateExpressionCode(
            context    = context,
            expression = contraction_body
        )

def generateContractionCode( contraction, context ):
    loop_var_codes = []

    for count, loop_var_assign in enumerate( contraction.getTargets() ):
        loop_var_code = generateAssignmentCode(
            targets   = loop_var_assign,
            value     = Generator.getContractionIterValueIdentifier(
                index   = count + 1,
                context = context
            ),
            context   = context
        )

        loop_var_codes.append( loop_var_code )

    contraction_code = _generatorContractionBodyCode(
        contraction = contraction.getBody(),
        context     = context
    )

    iterated_identifier = generateExpressionCode(
        expression = contraction.getSource0(),
        context    = context.getParent()
    )

    sub_iterated_identifiers = generateExpressionsCode(
        expressions = contraction.getInnerSources(),
        context     = context
    )

    contraction_condition_identifiers = []

    for condition in contraction.getConditions():
        contraction_condition_identifier = generateConditionCode(
            condition  = condition,
            allow_none = True,
            context    = context
        )

        contraction_condition_identifiers.append(
            contraction_condition_identifier
        )

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

    return Generator.getContractionCallCode(
        contraction_identifier = contraction_identifier,
        is_generator           = contraction.isExpressionGeneratorBuilder(),
        contraction_iterated   = iterated_identifier,
        closure_var_codes      = Generator.getClosureVariableProvisionCode(
            closure_variables = contraction.getClosureVariables(),
            context           = context.getParent()
        )
    )

def generateListContractionCode( contraction, context ):
    # Have a separate context to create list contraction code.
    contraction_context = Contexts.PythonListContractionContext(
        parent = context
    )

    return generateContractionCode(
        contraction = contraction,
        context     = contraction_context
    )

def generateSetContractionCode( contraction, context ):
    # Have a separate context to create list contraction code.
    contraction_context = Contexts.PythonSetContractionContext(
        parent = context
    )

    return generateContractionCode(
        contraction = contraction,
        context     = contraction_context
    )

def generateDictContractionCode( contraction, context ):
    # Have a separate context to create list contraction code.
    contraction_context = Contexts.PythonDictContractionContext(
        parent = context
    )

    return generateContractionCode(
        contraction = contraction,
        context     = contraction_context
    )

def generateGeneratorExpressionCode( generator_expression, context ):
    # Have a separate context to create generator expression code.
    generator_context = Contexts.PythonGeneratorExpressionContext(
        parent = context
    )

    return generateContractionCode(
        contraction = generator_expression,
        context     = generator_context
    )

def generateGeneratorExpressionBodyCode( generator_expression, context ):
    context = Contexts.PythonGeneratorExpressionContext(
        parent        = context,
        generator_def = generator_expression
    )

    codes = generateExpressionCode(
        expression = generator_expression.getBody(),
        context    = context
    )

    return context, codes

def generateLambdaCode( lambda_expression, context ):
    assert lambda_expression.isExpressionLambdaBuilder()

    lambda_context = Contexts.PythonLambdaExpressionContext(
        parent          = context,
        parameter_names = lambda_expression.getBody().getParameters().getParameterNames()
    )

    # TODO: Have a generateLambdaBodyCode function
    if not lambda_expression.getBody().isGenerator():
        code = Generator.getReturnCode(
            identifier = generateExpressionCode(
                expression = lambda_expression.getBody().getBody(),
                context    = lambda_context
            )
        )
    else:
        code = Generator.getStatementCode(
            identifier = Generator.getYieldCode(
                identifier = generateExpressionCode(
                    expression = lambda_expression.getBody().getBody(),
                    context    = lambda_context
                )
            )
        )

    # TODO: This ought to be done a bit prettier in a function for every user.
    if Options.shallHaveStatementLines():
        codes = [
            Generator.getCurrentLineCode( lambda_expression.getSourceReference() ),
            code
        ]
    else:
        codes = [ code ]

    context.addLambdaCodes(
        lambda_def     = lambda_expression,
        lambda_code    = codes,
        lambda_context = lambda_context
    )

    default_value_identifiers = []

    # TODO: There is a generateExpressionsCode is there?
    for default_parameter_value in lambda_expression.getDefaultExpressions():
        default_value_identifiers.append(
            generateExpressionCode(
                expression = default_parameter_value,
                context    = context
            )
        )

    code = Generator.getLambdaExpressionReferenceCode(
        lambda_expression = lambda_expression,
        context           = context,
        default_values    = default_value_identifiers
    )

    return code

def generateFunctionBodyCode( function, context ):
    body = function.getBody()

    context = Contexts.PythonFunctionContext(
        parent   = context,
        function = function
    )

    codes = generateStatementSequenceCode(
        context            = context,
        statement_sequence = body
    )

    return context, codes

def generateFunctionCode( function, context ):
    assert function.isFunctionBuilder()

    function_context, function_codes = generateFunctionBodyCode(
        function  = function.getBody(),
        context   = context
    )

    context.addFunctionCodes(
        function         = function,
        function_context = function_context,
        function_codes   = function_codes,
    )

    default_value_identifiers = []

    for _default_parameter_name, default_parameter_value in function.getDefaultParameters():
        default_value_identifiers.append(
            generateExpressionCode(
                expression = default_parameter_value,
                context    = context
            )
        )

    decorators = generateExpressionsCode(
        expressions = function.getDecorators(),
        context     = context
    )

    function_creation_identifier = Generator.getFunctionCreationCode(
        function       = function,
        decorators     = decorators,
        default_values = default_value_identifiers,
        context        = context
    )

    return generateAssignmentCode(
        targets = function.getTarget(),
        value   = function_creation_identifier,
        context = context
    )

def generateClassBodyCode( class_body, context ):
    context = Contexts.PythonClassContext(
        parent    = context,
        class_def = class_body
    )

    codes = generateStatementSequenceCode(
        context            = context,
        statement_sequence = class_body.getBody()
    )

    return context, codes


def generateClassCode( class_def, context ):
    assert class_def.isClassBuilder()

    bases_identifier = generateSequenceCreationCode(
        sequence_kind = "tuple",
        elements      = class_def.getBaseClasses(),
        context       = context
    )

    class_context, class_codes = generateClassBodyCode(
        class_body = class_def.getBody(),
        context    = context
    )

    dict_identifier = Generator.getClassDictCreationCode(
        class_def = class_def,
        context   = context
    )

    decorators = generateExpressionsCode(
        expressions = class_def.getDecorators(),
        context     = context
    )

    class_creation_identifier = Generator.getClassCreationCode(
        code_name        = class_def.getCodeName(),
        bases_identifier = bases_identifier,
        dict_identifier  = dict_identifier,
        decorators       = decorators
    )

    context.addClassCodes(
        class_def     = class_def,
        class_context = class_context,
        class_codes   = class_codes,
    )

    return generateAssignmentCode(
        targets = class_def.getTarget(),
        value   = class_creation_identifier,
        context = context
    )

def generateOperationCode( operator, operands, context ):
    return Generator.getOperationCode(
        operator    = operator,
        identifiers = generateExpressionsCode(
            expressions = operands,
            context     = context
        )
    )

def generateComparisonExpressionCode( comparison_expression, context ):
    return Generator.getComparisonExpressionCode(
        comparators = comparison_expression.getComparators(),
        operands    = generateExpressionsCode(
            expressions = comparison_expression.getOperands(),
            context     = context
        ),
        context     = context
    )

def generateDictionaryCreationCode( keys, values, context ):
    if _areConstants( keys ) and _areConstants( values ):
        constant = {}

        for key, value in zip( keys, values ):
            constant[ key.getConstant() ] = value.getConstant()

        return Generator.getConstantHandle(
            context  = context,
            constant = constant
        )
    else:
        key_identifiers = generateExpressionsCode(
            expressions = keys,
            context     = context
        )

        value_identifiers = generateExpressionsCode(
            expressions = values,
            context     = context
        )

        return Generator.getDictionaryCreationCode(
            keys    = key_identifiers,
            values  = value_identifiers,
        )

def generateSetCreationCode( values, context ):
    value_identifiers = generateExpressionsCode(
        expressions = values,
        context     = context
    )

    return Generator.getSetCreationCode(
        values  = value_identifiers
    )

def _areConstants( expressions ):
    for expression in expressions:
        if not expression.isConstantReference():
            return False

        if expression.isMutable():
            return False
    else:
        return True

def generateSliceRangeIdentifier( lower, upper, context ):
    if lower is None:
        lower = Generator.getMinIndexCode()
    else:
        lower = Generator.getIndexCode(
            identifier = generateExpressionCode(
                expression = lower,
                context    = context
            )
        )

    if upper is None:
        upper = Generator.getMaxIndexCode()
    else:
        upper = Generator.getIndexCode(
            identifier = generateExpressionCode(
                expression = upper,
                context    = context
            )
        )

    return lower, upper

def generateSliceAccessIdentifiers( sliced, lower, upper, context ):
    lower, upper = generateSliceRangeIdentifier( lower, upper, context )

    sliced = generateExpressionCode(
        expression = sliced,
        context    = context
    )

    return sliced, lower, upper

def generateFunctionCallCode( function, context ):
    function_identifier = generateExpressionCode(
        expression = function.getCalledExpression(),
        context    = context
    )

    positional_args_identifier = generateSequenceCreationCode(
        sequence_kind = "tuple",
        elements      = function.getPositionalArguments(),
        context       = context
    )

    named_arguments = function.getNamedArguments()

    # TODO: This should be moved to optimization stage.
    kw_identifier = generateDictionaryCreationCode(
        keys      = [
            Nodes.CPythonExpressionConstantRef(
                constant   = named_arg_desc[0],
                source_ref = function.getSourceReference()
            )
            for named_arg_desc in
            named_arguments
        ],
        values    = [ named_arg_desc[1] for named_arg_desc in named_arguments ],
        context   = context
    )

    star_list_identifier = generateExpressionCode(
        expression = function.getStarListArg(),
        allow_none = True,
        context    = context
    )

    star_dict_identifier = generateExpressionCode(
        expression = function.getStarDictArg(),
        allow_none = True,
        context    = context
    )

    # TODO: Try to predict and remove empty star_list_identifier and star_dict_identifier
    # so that the overhead associated can be eliminated. This probably should happen early
    # on.

    return Generator.getFunctionCallCode(
        function_identifier  = function_identifier,
        argument_tuple       = positional_args_identifier,
        argument_dictionary  = kw_identifier,
        star_list_identifier = star_list_identifier,
        star_dict_identifier = star_dict_identifier,
    )

def _decideLocalsMode( provider ):
    if provider.isClassBody():
        mode = "updated"
    elif provider.isFunctionBody() and provider.isExecContaining():
        mode = "updated"
    else:
        mode = "copy"

    return mode

def generateBuiltinLocalsCode( locals_node, context ):
    provider = locals_node.getParentVariableProvider()

    return Generator.getLoadLocalsCode(
        context  = context,
        provider = provider,
        mode     = _decideLocalsMode( provider )
    )

def generateBuiltinDirCode( dir_node, context ):
    provider = dir_node.getParentVariableProvider()

    return Generator.getLoadDirCode(
        context  = context,
        provider = provider
    )


def generateExpressionsCode( expressions, context, allow_none = False ):
    assert type( expressions ) in ( tuple, list )

    return [
        generateExpressionCode(
            expression = expression,
            context    = context,
            allow_none = allow_none
        )
        for expression in
        expressions
    ]

def generateExpressionCode( expression, context, allow_none = False ):
    # This is a dispatching function with a branch per expression node type.
    # pylint: disable=R0912

    if expression is None and allow_none:
        return None

    def makeExpressionCode( expression, allow_none = False ):
        if allow_none and expression is None:
            return None

        return generateExpressionCode(
            expression = expression,
            context    = context
        )

    if not expression.isExpression():
        print( "No expression", expression )

        expression.dump()
        assert False, expression

    if expression.isVariableReference():
        if expression.getVariable() is None:
            print( "Illegal variable reference, not resolved" )

            expression.dump()
            assert False, expression.getSourceReference()

        identifier = Generator.getVariableHandle(
            variable = expression.getVariable(),
            context  = context
        )
    elif expression.isConstantReference():
        identifier = Generator.getConstantAccess(
            constant = expression.getConstant(),
            context  = context
        )
    elif expression.isOperation():
        identifier = generateOperationCode(
            operator  = expression.getOperator(),
            operands  = expression.getOperands(),
            context   = context
        )
    elif expression.isSequenceCreation():
        identifier = generateSequenceCreationCode(
            sequence_kind = expression.getSequenceKind(),
            elements      = expression.getElements(),
            context       = context
        )
    elif expression.isDictionaryCreation():
        identifier = generateDictionaryCreationCode(
            keys      = expression.getKeys(),
            values    = expression.getValues(),
            context   = context
        )
    elif expression.isSetCreation():
        identifier = generateSetCreationCode(
            values    = expression.getValues(),
            context   = context
        )
    elif expression.isFunctionCall():
        identifier = generateFunctionCallCode(
            function = expression,
            context    = context
        )
    elif expression.isListContractionBuilder():
        identifier = generateListContractionCode(
            contraction = expression,
            context     = context
        )
    elif expression.isSetContractionBuilder():
        identifier = generateSetContractionCode(
            contraction = expression,
            context     = context
        )
    elif expression.isDictContractionBuilder():
        identifier = generateDictContractionCode(
            contraction = expression,
            context     = context
        )
    elif expression.isAttributeLookup():
        attribute_name = mangleAttributeName(
            attribute_name = expression.getAttributeName(),
            node           = expression
        )

        identifier = Generator.getAttributeLookupCode(
            attribute = context.getConstantHandle( attribute_name ),
            source    = makeExpressionCode( expression.getLookupSource() ),
        )
    elif expression.isSubscriptLookup():
        identifier = Generator.getSubscriptLookupCode(
            subscript = generateExpressionCode(
                expression = expression.getSubscript(),
                context    = context
            ),
            source    = generateExpressionCode(
                expression = expression.getLookupSource(),
                context    = context
            )
        )
    elif expression.isSliceLookup():
        expression_identifier, lower_identifier, upper_identifier = generateSliceAccessIdentifiers(
            sliced    = expression.getLookupSource(),
            lower     = expression.getLower(),
            upper     = expression.getUpper(),
            context   = context
        )

        identifier = Generator.getSliceLookupCode(
            source  = expression_identifier,
            lower   = lower_identifier,
            upper   = upper_identifier
        )

    elif expression.isSliceObjectExpression():
        identifier = Generator.getSliceObjectCode(
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
            )
        )
    elif expression.isConditionOR():
        identifier = Generator.getSelectionOrCode(
            conditions = generateExpressionsCode(
                expressions = expression.getExpressions(),
                context = context
            )
        )

    elif expression.isConditionAND():
        identifier = Generator.getSelectionAndCode(
            conditions = generateExpressionsCode(
                expressions = expression.getExpressions(),
                context = context
            )
        )
    elif expression.isConditionNOT():
        identifier = Generator.getConditionNotCode(
            condition = makeExpressionCode( expression = expression.getExpression() )
        )
    elif expression.isConditionalExpression():
        identifier = Generator.getConditionalExpressionCode(
            condition = generateConditionCode(
                condition = expression.getCondition(),
                context   = context
            ),
            codes_yes = makeExpressionCode( expression.getExpressionYes() ),
            codes_no  = makeExpressionCode( expression.getExpressionNo() )
        )
    elif expression.isBuiltinRange():
        identifier = Generator.getBuiltinRangeCode(
            low  = makeExpressionCode( expression.getLow(), allow_none = False ),
            high = makeExpressionCode( expression.getHigh(), allow_none = True ),
            step = makeExpressionCode( expression.getStep(), allow_none = True )
        )
    elif expression.isBuiltinGlobals():
        identifier = Generator.getLoadGlobalsCode(
            context = context
        )
    elif expression.isBuiltinLocals():
        identifier = generateBuiltinLocalsCode(
            locals_node = expression,
            context     = context
        )
    elif expression.isBuiltinDir():
        identifier = generateBuiltinDirCode(
            dir_node = expression,
            context  = context
        )
    elif expression.isBuiltinVars():
        identifier = Generator.getLoadVarsCode(
            identifier = makeExpressionCode( expression.getSource() )
        )
    elif expression.isBuiltinEval():
        identifier = generateEvalCode(
            context         = context,
            eval_expression = expression
        )
    elif expression.isBuiltinOpen():
        identifier = Generator.getBuiltinOpenCode(
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
            )
        )
    elif expression.isExpressionLambdaBuilder():
        identifier = generateLambdaCode(
            lambda_expression = expression,
            context           = context
        )
    elif expression.isExpressionGeneratorBuilder():
        identifier = generateGeneratorExpressionCode(
            generator_expression = expression,
            context              = context
        )
    elif expression.isExpressionComparison():
        identifier = generateComparisonExpressionCode(
            comparison_expression = expression,
            context               = context
        )
    elif expression.isExpressionYield():
        yielded = expression.getExpression()

        # TODO: The "None" possibility is a wart of code generation that should be removed
        # in tree building already.
        if yielded is not None:
            identifier = Generator.getYieldCode(
                identifier = makeExpressionCode( yielded )
            )
        else:
            identifier = Generator.getYieldCode(
                identifier = context.getConstantHandle(
                    constant = None
                )
            )
    elif expression.isBuiltinImport():
        identifier = generateImportBuiltinCode(
            expression = expression,
            context    = context
        )
    elif expression.isBuiltinChr():
        identifier = Generator.getBuiltinChrCode(
            value   = makeExpressionCode( expression.getValue() )
        )
    elif expression.isBuiltinOrd():
        identifier = Generator.getBuiltinOrdCode(
            value   = makeExpressionCode( expression.getValue() )
        )
    elif expression.isBuiltinLen():
        identifier = Generator.getBuiltinLenCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif expression.isBuiltinType1():
        identifier = Generator.getBuiltinType1Code(
            value   = makeExpressionCode( expression.getValue() )
        )
    elif expression.isBuiltinType3():
        identifier = Generator.getBuiltinType3Code(
            name_identifier  = makeExpressionCode( expression.getTypeName() ),
            bases_identifier = makeExpressionCode( expression.getBases() ),
            dict_identifier  = makeExpressionCode( expression.getDict() ),
            context          = context
        )
    else:
        assert False, expression

    if not hasattr( identifier, "getCodeTemporaryRef" ):
        assert False, identifier

    return identifier


def generateAssignmentCode( targets, value, context, recursion = 1 ):
    # This is a dispatching function with a branch per assignment node type.
    # pylint: disable=R0912

    if type( targets ) not in ( tuple, list ) and targets.isAssignToSomething():
        targets = [ targets ]

    if len( targets ) == 1 and not targets[0].isAssignToTuple():
        assign_source = value
        code = ""

        brace = False
    else:
        if value.getCheapRefCount() == 1:
            code = "PyObjectTemporary _python_rvalue_%d( %s );\n" % ( recursion, value.getCodeExportRef() )
            assign_source = Generator.Identifier( "_python_rvalue_%d.asObject()" % recursion, 0 )
        else:
            code = "PyObject *_python_rvalue_%d = %s;\n" % ( recursion, value.getCodeTemporaryRef() )
            assign_source = Generator.Identifier( "_python_rvalue_%d" % recursion, 0 )

        brace = True

    iterator_identifier = None

    for target in targets:
        if target.isAssignToSubscript():
            code += Generator.getSubscriptAssignmentCode(
                subscribed    = generateExpressionCode(
                    expression = target.getSubscribed(),
                    context    = context
                ),
                subscript     = generateExpressionCode(
                    expression = target.getSubscript(),
                    context    = context
                ),
                identifier    = assign_source
            )

            code += "\n"
        elif target.isAssignToAttribute():
            attribute_name = mangleAttributeName(
                attribute_name = target.getAttributeName(),
                node           = target
            )

            code += Generator.getAttributeAssignmentCode(
                target     = generateExpressionCode(
                    expression = target.getLookupSource(),
                    context    = context
                ),
                attribute  = context.getConstantHandle(
                    constant = attribute_name
                ),
                identifier = assign_source
            )

            code += "\n"
        elif target.isAssignToSlice():
            expression_identifier, lower_identifier, upper_identifier = generateSliceAccessIdentifiers(
                sliced    = target.getLookupSource(),
                lower     = target.getLower(),
                upper     = target.getUpper(),
                context   = context
            )

            code += Generator.getSliceAssignmentCode(
                target     = expression_identifier,
                upper      = upper_identifier,
                lower      = lower_identifier,
                identifier = assign_source
            )

            code += "\n"
        elif target.isAssignToVariable():
            code += Generator.getAssignmentCode(
                variable   = target.getTargetVariableRef().getVariable(),
                identifier = assign_source,
                context    = context
            )

            code += "\n"
        elif target.isAssignToTuple():
            elements = target.getElements()

            # Unpack if it's the first time.
            if iterator_identifier is None:
                iterator_identifier = Generator.getTupleUnpackIteratorCode( recursion )

                lvalue_identifiers = [
                    Generator.getTupleUnpackLeftValueCode( recursion, count+1 )
                    for count in
                    range( len( elements ))
                ]

                code += Generator.getUnpackTupleCode(
                    assign_source       = assign_source,
                    iterator_identifier = iterator_identifier,
                    lvalue_identifiers  = lvalue_identifiers
                )


            # TODO: If an assigments goes to an increasing/decreasing length of elements
            # raise an exception. For the time being, just ignore it.
            for count, element in enumerate( elements ):
                code += generateAssignmentCode(
                    targets   = element,
                    value     = lvalue_identifiers[ count ],
                    context   = context,
                    recursion = recursion + 1
                )

            if not code.endswith( "\n" ):
                code += "\n"

        else:
            assert False, (target, target.getSourceReference())

    assert code.endswith( "\n" ), repr( code )

    if brace:
        code = Generator.getBlockCode( code[:-1] )

    if recursion == 1:
        code = code.rstrip()

    return code

def generateDelCode( targets, context ):
    code = ""

    def makeExpressionCode( expression, allow_none = False ):
        if allow_none and expression is None:
            return None

        return generateExpressionCode(
            expression = expression,
            context    = context
        )

    for target in targets:
        if target.isAssignToSubscript():
            code += Generator.getSubscriptDelCode(
                subscribed = makeExpressionCode( target.getSubscribed() ),
                subscript  = makeExpressionCode( target.getSubscript() )
            )
        elif target.isAssignToAttribute():
            attribute_name = mangleAttributeName(
                attribute_name = target.getAttributeName(),
                node           = target
            )

            code += Generator.getAttributeDelCode(
                target    = makeExpressionCode( target.getLookupSource() ),
                attribute = context.getConstantHandle( constant = attribute_name )
            )
        elif target.isAssignToVariable():
            code += Generator.getVariableDelCode(
                variable = target.getTargetVariableRef().getVariable(),
                context  = context
            )
        elif target.isAssignToTuple():
            elements = target.getElements()

            for element in elements:
                code += generateDelCode(
                    targets   = [ element ],
                    context   = context
                )

        elif target.isAssignToSlice():
            code += Generator.getSliceDelCode(
                target     = makeExpressionCode( target.getLookupSource() ),
                upper      = makeExpressionCode( target.getUpper(), allow_none = True ),
                lower      = makeExpressionCode( target.getLower(), allow_none = True )
            )
        else:
            assert False, target

    return code

def generateEvalCode( eval_expression, context ):
    exec_globals = eval_expression.getGlobals()

    if exec_globals is None:
        globals_identifier = Generator.getConstantHandle( constant = None, context = context )
    else:
        globals_identifier = generateExpressionCode(
            expression = exec_globals,
            context    = context
        )

    exec_locals = eval_expression.getLocals()

    if exec_locals is None:
        locals_identifier = Generator.getConstantHandle( constant = None, context = context )
    else:
        locals_identifier = generateExpressionCode(
            expression = exec_locals,
            context    = context
        )

    identifier = Generator.getEvalCode(
        exec_code          = generateExpressionCode(
            expression   = eval_expression.getSourceCode(),
            context      = context
        ),
        globals_identifier = globals_identifier,
        locals_identifier  = locals_identifier,
        future_flags       = Generator.getFutureFlagsCode(
            future_spec = eval_expression.getSourceReference().getFutureSpec()
        ),
        provider           = eval_expression.getParentVariableProvider(),
        context            = context
    )

    return identifier

def generateExecCode( exec_def, context ):
    exec_globals = exec_def.getGlobals()

    if exec_globals is None:
        globals_identifier = Generator.getConstantHandle(
            constant = None,
            context  = context
        )
    else:
        globals_identifier = generateExpressionCode(
            expression = exec_globals,
            context    = context
        )

    exec_locals = exec_def.getLocals()

    if exec_locals is None:
        locals_identifier = Generator.getConstantHandle(
            constant = None,
            context  = context
        )
    elif exec_locals is not None:
        locals_identifier = generateExpressionCode(
            expression = exec_locals,
            context    = context
        )

    return Generator.getExecCode(
        context            = context,
        provider           = exec_def.getParentVariableProvider(),
        exec_code          = generateExpressionCode(
            context    = context,
            expression = exec_def.getSourceCode()
        ),
        globals_identifier = globals_identifier,
        locals_identifier  = locals_identifier,
        future_flags       = Generator.getFutureFlagsCode(
            future_spec = exec_def.getSourceReference().getFutureSpec()
        )
    )

def generateExecCodeInline( exec_def, context ):
    exec_context = Contexts.PythonExecInlineContext(
        parent = context
    )

    codes = generateStatementSequenceCode(
        statement_sequence = exec_def.getBody(),
        context            = exec_context
    )

    return Generator.getBlockCode(
        codes = codes
    )

def generateTryExceptCode( statement, context ):
    exception_identifiers = generateExpressionsCode(
        expressions = statement.getExceptionCatchers(),
        allow_none  = True,
        context     = context
    )

    exception_assignments = []

    for assign in statement.getExceptionAssigns():
        if assign is not None:
            exception_assignments.append(
                generateAssignmentCode(
                    targets   = assign,
                    value     = Generator.getCurrentExceptionObjectCode(),
                    context   = context
                )
            )
        else:
            exception_assignments.append( None )

    catcher_codes = []

    for catched in statement.getExceptionCatchBranches():
        catcher_codes.append(
            generateStatementSequenceCode(
                statement_sequence = catched,
                context            = context
            )
        )

    no_raise = statement.getBlockNoRaise()

    if no_raise is not None:
        else_code = generateStatementSequenceCode(
            statement_sequence = no_raise,
            context            = context
        )
    else:
        else_code = None

    return Generator.getTryExceptCode(
        context               = context,
        code_tried            = generateStatementSequenceCode(
            statement_sequence = statement.getBlockTry(),
            context            = context,
        ),
        exception_identifiers = exception_identifiers,
        exception_assignments = exception_assignments,
        catcher_codes         = catcher_codes,
        else_code             = else_code
    )

def generateRaiseCode( statement, context ):
    parameters = statement.getExceptionParameters()

    if len( parameters ) == 0:
        return Generator.getReRaiseExceptionCode(
            local = statement.isReraiseExceptionLocal()
        )
    elif len( parameters ) == 1:
        return Generator.getRaiseExceptionCode(
            exception_type_identifier  = generateExpressionCode(
                expression = parameters[0],
                context    = context
            ),
            exception_value_identifier = None,
            exception_tb_identifier    = None,
            exception_tb_maker         = Generator.getTracebackMakingIdentifier(
                context = context,
                line    = statement.getSourceReference().getLineNumber()
            )
        )
    elif len( parameters ) == 2:
        return Generator.getRaiseExceptionCode(
            exception_type_identifier = generateExpressionCode(
                expression = parameters[0],
                context    = context
            ),
            exception_value_identifier = generateExpressionCode(
                expression = parameters[1],
                context    = context
            ),
            exception_tb_identifier    = None,
            exception_tb_maker         = Generator.getTracebackMakingIdentifier(
                context = context,
                line    = statement.getSourceReference().getLineNumber()
            )
        )
    elif len( parameters ) == 3:
        return Generator.getRaiseExceptionCode(
            exception_type_identifier  = generateExpressionCode(
                expression = parameters[0],
                context    = context
            ),
            exception_value_identifier = generateExpressionCode(
                expression = parameters[1],
                context    = context
            ),
            exception_tb_identifier    = generateExpressionCode(
                expression = parameters[2],
                context    = context
            ),
            exception_tb_maker         = None
        )
    else:
        assert False, parameters


def generateImportBuiltinCode( expression, context ):
    return Generator.getImportModuleCode(
        context     = context,
        module_name = expression.getModuleName(),
        import_name = expression.getImportName(),
        import_list = Generator.getEmptyImportListCode()
    )

def generateImportExternalCode( statement, context ):
    return generateAssignmentCode(
        targets = statement.getTarget(),
        value   = generateImportBuiltinCode(
            expression = statement,
            context    = context
        ),
        context = context
    )

def generateImportEmbeddedCode( statement, context ):
    return generateAssignmentCode(
        targets = statement.getTarget(),
        value   = Generator.getImportEmbeddedCode(
            module_name = statement.getModuleName(),
            import_name = statement.getImportName(),
            context     = context
        ),
        context = context
    )

def _generateImportFromLookupCode( statement, context ):
    module_temp = Generator.getImportFromModuleTempIdentifier()

    lookup_code = ""

    for object_name, target in zip( statement.getImports(), statement.getTargets() ):
        assert object_name != "*"

        lookup_code += generateAssignmentCode(
            targets = target,
            value   = Generator.getAttributeLookupCode(
                source    = module_temp,
                attribute =  context.getConstantHandle(
                    constant = object_name
                )
            ),
            context = context
        )

    return lookup_code


def generateImportFromExternalCode( statement, context ):
    lookup_code = _generateImportFromLookupCode(
        statement = statement,
        context   = context
    )

    return Generator.getImportFromCode(
        module_name    = statement.getModuleName(),
        lookup_code    = lookup_code,
        import_list    = statement.getImports(),
        embedded       = False,
        sub_modules    = (),
        context        = context,
    )


def generateImportFromEmbeddedCode( statement, context ):
    lookup_code = _generateImportFromLookupCode(
        statement = statement,
        context   = context
    )

    return Generator.getImportFromCode(
        module_name    = statement.getModuleName(),
        lookup_code    = lookup_code,
        import_list    = statement.getImports(),
        embedded       = True,
        sub_modules    = [
            sub_module.getFullName()
            for sub_module in
            statement.getSubModules()
        ],
        context        = context,
    )


def generateImportStarExternalCode( statement, context ):
    return Generator.getImportFromStarCode(
        module_name = statement.getModuleName(),
        embedded    = False,
        context     = context
    )

def generateImportStarEmbeddedCode( statement, context ):
    return Generator.getImportFromStarCode(
        module_name = statement.getModuleName(),
        embedded    = True,
        context     = context
    )


def generateStatementCode( statement, context ):
    try:
        return _generateStatementCode( statement, context )
    except:
        print( "Problem with", statement, "at", statement.getSourceReference() )
        raise

def _generateStatementCode( statement, context ):
    # This is a dispatching function with a branch per statement node type.
    # pylint: disable=R0912

    if not statement.isStatement():
        statement.dump()
        assert False

    def makeExpressionCode( expression, allow_none = False ):
        if allow_none and expression is None:
            return None

        return generateExpressionCode(
            expression = expression,
            context     = context
        )

    if statement.isStatementAssignment():
        source = statement.getSource()

        if source is not None:
            code = generateAssignmentCode(
                targets   = statement.getTargets(),
                value     = makeExpressionCode( source ),
                context   = context
            )
        else:
            code = generateDelCode(
                targets   = statement.getTargets(),
                context   = context
            )
    elif statement.isStatementInplaceAssignment():
        target = statement.getTarget()

        if target.isAssignToVariable():
            code = Generator.getInplaceVarAssignmentCode(
                variable   = target.getTargetVariableRef().getVariable(),
                operator   = statement.getOperator(),
                identifier = makeExpressionCode( statement.getExpression() ),
                context    = context
            )
        elif target.isAssignToSubscript():
            code = Generator.getInplaceSubscriptAssignmentCode(
                subscribed = makeExpressionCode(
                    expression = target.getSubscribed()
                ),
                subscript  = makeExpressionCode(
                    expression = target.getSubscript()
                ),
                operator   = statement.getOperator(),
                identifier = makeExpressionCode( statement.getExpression() )
            )
        elif target.isAssignToAttribute():
            attribute_name = mangleAttributeName(
                attribute_name = target.getAttributeName(),
                node           = target
            )

            code = Generator.getInplaceAttributeAssignmentCode(
                target     = makeExpressionCode(
                    expression = target.getLookupSource()
                ),
                attribute  = context.getConstantHandle( attribute_name ),
                operator   = statement.getOperator(),
                identifier = makeExpressionCode( statement.getExpression() )
            )
        elif target.isAssignToSlice():
            target_identifier, lower_identifier, upper_identifier = generateSliceAccessIdentifiers(
                sliced    = target.getLookupSource(),
                lower     = target.getLower(),
                upper     = target.getUpper(),
                context   = context
            )

            code = Generator.getInplaceSliceAssignmentCode(
                target     = target_identifier,
                lower      = lower_identifier,
                upper      = upper_identifier,
                operator   = statement.getOperator(),
                identifier = makeExpressionCode( statement.getExpression() )
            )
        else:
            assert False, ( "not supported for inplace assignment", target, target.getSourceReference() )
    elif statement.isFunctionBuilder():
        code = generateFunctionCode(
            function  = statement,
            context   = context
        )
    elif statement.isClassBuilder():
        code = generateClassCode(
            class_def = statement,
            context   = context
        )
    elif statement.isStatementExpression():
        code = Generator.getStatementCode(
            identifier = makeExpressionCode( statement.getExpression() )
        )
    elif statement.isStatementPrint():
        if statement.getDestination() is not None:
            target_file = makeExpressionCode( statement.getDestination() )
        else:
            target_file = None

        values = generateExpressionsCode(
            context     = context,
            expressions = statement.getValues()
        )

        code = Generator.getPrintCode(
            target_file = target_file,
            identifiers = values,
            newline     = statement.isNewlinePrint()
        )
    elif statement.isStatementReturn():
        parent_function = statement.getParentFunction()

        if parent_function is not None and parent_function.isGenerator():
            code = Generator.getYieldTerminatorCode()
        else:
            expression = statement.getExpression()

            # TODO: The "None" possibility is a wart of code generation that should be
            # removed in tree building already.
            if expression is not None:
                code = Generator.getReturnCode(
                    identifier = makeExpressionCode( expression )
                )
            else:
                code = Generator.getReturnCode(
                    identifier = context.getConstantHandle(
                        constant = None
                    )
                )
    elif statement.isStatementWith():
        body_codes = generateStatementSequenceCode(
            statement_sequence = statement.getWithBody(),
            context            = context
        )

        with_manager_identifier, with_value_identifier = Generator.getWithNames(
            context = context
        )

        if statement.getTarget() is not None:
            assign_codes = generateAssignmentCode(
                targets    = statement.getTarget(),
                value      = with_value_identifier,
                context    = context
            )
        else:
            assign_codes = None

        code = Generator.getWithCode(
            source_identifier       = makeExpressionCode( statement.getExpression() ),
            assign_codes            = assign_codes,
            with_manager_identifier = with_manager_identifier,
            with_value_identifier   = with_value_identifier,
            body_codes              = body_codes,
            context                 = context
        )
    elif statement.isStatementForLoop():
        iter_name, iter_value, iter_object = Generator.getForLoopNames( context = context )

        iterator = Generator.getIteratorCreationCode(
            iterated = makeExpressionCode( statement.getIterated() )
        )

        assignment_code = generateAssignmentCode(
            targets   = statement.getLoopVariableAssignment(),
            value     = iter_object,
            context   = context
        )

        loop_body_codes = generateStatementSequenceCode(
            statement_sequence = statement.getBody(),
            context            = context
        )

        if statement.getNoBreak() is not None:
            loop_else_codes = generateStatementSequenceCode(
                statement_sequence = statement.getNoBreak(),
                context            = context
            )
        else:
            loop_else_codes = []

        line_number_code = Generator.getCurrentLineCode( statement.getIterated().getSourceReference() ) if Options.shallHaveStatementLines() else ""

        code = Generator.getForLoopCode(
            line_number_code = line_number_code,
            iterator         = iterator,
            iter_name        = iter_name,
            iter_value       = iter_value,
            iter_object      = iter_object,
            loop_var_code    = assignment_code,
            loop_body_codes  = loop_body_codes,
            loop_else_codes  = loop_else_codes,
            needs_exceptions = statement.needsExceptionBreakContinue(),
            context          = context
        )
    elif statement.isStatementWhileLoop():
        loop_body_codes = generateStatementSequenceCode(
            statement_sequence = statement.getLoopBody(),
            context            = context
        )

        if statement.getNoEnter() is not None:
            loop_else_codes = generateStatementSequenceCode(
                statement_sequence = statement.getNoEnter(),
                context            = context
            )
        else:
            loop_else_codes = []

        code = Generator.getWhileLoopCode(
            condition        = generateConditionCode(
                condition = statement.getCondition(),
                context   = context
            ),
            loop_body_codes  = loop_body_codes,
            loop_else_codes  = loop_else_codes,
            context          = context,
            needs_exceptions = statement.needsExceptionBreakContinue(),
        )
    elif statement.isStatementConditional():
        branches_codes = []

        for branch in statement.getBranches():
            branch_codes = generateStatementSequenceCode(
                statement_sequence = branch,
                context            = context
            )

            branches_codes.append( branch_codes )

        # TODO: We don't need generator to provide very generic if/elif/else, only
        # if/else, the node tree contains nothing else.
        code = Generator.getBranchCode(
            conditions     = [
                generateConditionCode(
                    condition = statement.getCondition(),
                    context   = context
                )
            ],
            branches_codes = branches_codes
        )
    elif statement.isStatementContinue():
        code = Generator.getLoopContinueCode(
            needs_exceptions = statement.needsExceptionBreakContinue()
        )
    elif statement.isStatementBreak():
        code = Generator.getLoopBreakCode(
            needs_exceptions = statement.needsExceptionBreakContinue()
        )
    elif statement.isStatementImportExternal():
        return generateImportExternalCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementImportEmbedded():
        return generateImportEmbeddedCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementImportFromExternal():
        return generateImportFromExternalCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementImportFromEmbedded():
        return generateImportFromEmbeddedCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementImportStarExternal():
        return generateImportStarExternalCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementImportStarEmbedded():
        return generateImportStarEmbeddedCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementTryFinally():
        code = Generator.getTryFinallyCode(
            context     = context,
            code_tried = generateStatementSequenceCode(
                statement_sequence = statement.getBlockTry(),
                context            = context
            ),
            code_final = generateStatementSequenceCode(
                statement_sequence = statement.getBlockFinal(),
                context            = context
            )
        )
    elif statement.isStatementTryExcept():
        code = generateTryExceptCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementRaiseException():
        code = generateRaiseCode(
            statement = statement,
            context   = context
        )

    elif statement.isStatementAssert():
        code = Generator.getAssertCode(
            condition_identifier = generateConditionCode(
                condition = statement.getExpression(),
                inverted  = True,
                context   = context
            ),
            failure_identifier   = makeExpressionCode( statement.getArgument(), allow_none = True ),
            exception_tb_maker   = Generator.getTracebackMakingIdentifier(
                context = context,
                line    = statement.getSourceReference().getLineNumber()
            )
        )
    elif statement.isStatementExec():
        code = generateExecCode(
            exec_def     = statement,
            context      = context
        )
    elif statement.isStatementExecInline():
        code = generateExecCodeInline(
            exec_def     = statement,
            context      = context
        )
    elif statement.isStatementDeclareGlobal():
        code = ""
    elif statement.isStatementPass():
        code = ""
    else:
        assert False, statement.__class__

    assert code == code.strip(), ( statement, "'%s'" % code )

    return code

def generateStatementSequenceCode( statement_sequence, context ):
    assert statement_sequence.isStatementsSequence(), statement_sequence

    statements = statement_sequence.getStatements()

    codes = []

    last_ref = None

    for statement in statements:
        if Options.shallTraceExecution():
            codes.append(
                Generator.getStatementTrace(
                    statement.getSourceReference().getAsString(),
                    repr( statement )
                )
            )

        code = generateStatementCode(
            statement = statement,
            context   = context
        )

        # Can happen for "global" declarations, these are still in the node tree and yield
        # no code.
        if code == "":
            continue

        source_ref = statement.getSourceReference()

        if Options.shallHaveStatementLines() and source_ref != last_ref:
            code = Generator.getCurrentLineCode( source_ref ) + code
            last_ref = source_ref

        statement_codes = code.split( "\n" )

        assert statement_codes[0].strip() != "", ( "Code '%s'" % code, statement )

        codes += statement_codes

    return codes

def generateModuleCode( module, module_name, global_context, stand_alone ):
    assert module.isModule()

    context = Contexts.PythonModuleContext(
        module_name    = module_name,
        code_name      = Generator.getModuleIdentifier( module_name ),
        filename       = module.getFilename(),
        global_context = global_context,
    )

    statement_sequence = module.getBody()

    codes = generateStatementSequenceCode(
        statement_sequence = statement_sequence,
        context            = context
    )

    if module.isPackage():
        # TODO: For easier optimization, values for module attributes should be queried
        # from the module object with their name, like __path__ here.

        path_identifier = context.getConstantHandle(
            constant = [ Utils.dirname( module.getFilename() ) ]
        )
    else:
        path_identifier = None

    return Generator.getModuleCode(
        module_name         = module_name,
        package_name        = module.getPackage(),
        stand_alone         = stand_alone,
        doc_identifier      = context.getConstantHandle(
            constant = module.getDoc()
        ),
        filename_identifier = context.getConstantHandle(
            constant = module.getFilename()
        ),
        path_identifier     = path_identifier,
        codes               = codes,
        context             = context,
    )
