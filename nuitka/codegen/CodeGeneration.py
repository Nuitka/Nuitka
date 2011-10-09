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

from . import (
    Generator,
    Contexts,
)

from nuitka import (
    Constants,
    Tracing,
    Options
)

def mangleAttributeName( attribute_name, node ):
    if not attribute_name.startswith( "__" ) or attribute_name.endswith( "__" ):
        return attribute_name

    seen_function = False

    while node is not None:
        node = node.getParent()

        if node is None:
            break

        if node.isExpressionClassBody():
            if seen_function:
                return "_" + node.getName() + attribute_name
            else:
                return attribute_name
        elif node.isExpressionFunctionBody():
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
            element_identifiers = identifiers,
            context             = context
        )

def generateConditionCode( condition, context, inverted = False, allow_none = False ):
    # The complexity is needed to avoid unnecessary complex generated C++, so
    # e.g. inverted is typically a branch inside every optimizable case. pylint: disable=R0912

    if condition is None and allow_none:
        assert not inverted

        result = Generator.getTrueExpressionCode()
    elif condition.isExpressionConstantRef():
        value = condition.getConstant()

        if inverted:
            value = not value

        if value:
            result = Generator.getTrueExpressionCode()
        else:
            result = Generator.getFalseExpressionCode()
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
    elif condition.isExpressionBoolAND():
        parts = []

        for expression in condition.getExpressions():
            parts.append(
                generateConditionCode(
                    condition = expression,
                    context   = context
                )
            )

        result = Generator.getConditionAndCode( parts )

        if inverted:
            result = Generator.getConditionNotBoolCode(
                condition = result
            )
    elif condition.isExpressionBoolOR():
        parts = []

        for expression in condition.getExpressions():
            parts.append(
                generateConditionCode(
                    condition = expression,
                    context   = context
                )
            )

        result = Generator.getConditionOrCode( parts )

        if inverted:
            result = Generator.getConditionNotBoolCode(
                condition = result
            )
    else:
        condition_identifier = generateExpressionCode(
            context    = context,
            expression = condition
        )

        if inverted:
            result = Generator.getConditionCheckFalseCode(
                condition = condition_identifier
            )
        else:
            result = Generator.getConditionCheckTrueCode(
                condition = condition_identifier
            )

    return result

def _generatorContractionBodyCode( contraction, context ):
    contraction_body = contraction.getBody()

    # Dictionary contractions produce a tuple always.
    if contraction.isExpressionDictContractionBody():
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
    # Contractions have many details, pylint: disable=R0914

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

    if Options.shallHaveStatementLines():
        line_number_code = Generator.getCurrentLineCode(
            source_ref = contraction.getSourceReference()
        )
    else:
        line_number_code = ""


    if contraction.isExpressionGeneratorBuilder():
        assert len( contraction.getTargets() ) == len( sub_iterated_identifiers ) + 1

        contraction_decl = Generator.getFunctionDecl(
            function_identifier = contraction_identifier,
            decorator_count     = 0,
            default_identifiers = (),
            closure_variables   = contraction.getClosureVariables(),
            is_genexpr          = True,
            context             = context
        )

        contraction_code = Generator.getGeneratorExpressionCode(
            context              = context,
            generator_name       = "genexpr" if Options.isFullCompat() else contraction.getBody().getFullName(),
            generator_filename   = contraction.getParentModule().getFilename(),
            generator_identifier = contraction_identifier,
            generator_code       = contraction_code,
            generator_conditions = contraction_condition_identifiers,
            generator_iterateds  = sub_iterated_identifiers,
            loop_var_codes       = loop_var_codes,
            line_number_code     = line_number_code,
            closure_variables    = contraction.getClosureVariables(),
            provided_variables   = contraction.getProvidedVariables()
        )
    else:
        if contraction.isExpressionListContractionBuilder():
            contraction_kind = "list"
        elif contraction.isExpressionSetContractionBuilder():
            contraction_kind = "set"
        elif contraction.isExpressionDictContractionBuilder():
            contraction_kind = "dict"
        else:
            assert False

        contraction_decl = Generator.getContractionDecl(
            contraction_identifier = contraction_identifier,
            closure_variables      = contraction.getClosureVariables(),
            context                = context
        )

        contraction_code = Generator.getContractionCode(
            contraction_identifier = contraction_identifier,
            contraction_kind       = contraction_kind,
            contraction_code       = contraction_code,
            contraction_conditions = contraction_condition_identifiers,
            contraction_iterateds  = sub_iterated_identifiers,
            loop_var_codes         = loop_var_codes,
            closure_variables      = contraction.getClosureVariables(),
            provided_variables     = contraction.getProvidedVariables(),
            context                = context
        )

    context.addContractionCodes(
        code_name        = contraction.getCodeName(),
        contraction_decl = contraction_decl,
        contraction_code = contraction_code
    )

    return Generator.getContractionCallCode(
        contraction_identifier = contraction_identifier,
        is_genexpr             = contraction.isExpressionGeneratorBuilder(),
        contraction_iterated   = iterated_identifier,
        closure_var_codes      = Generator.getClosureVariableProvisionCode(
            closure_variables = contraction.getClosureVariables(),
            context           = context.getParent()
        )
    )

def generateListContractionCode( contraction, context ):
    # Have a separate context to create list contraction code.
    contraction_context = Contexts.PythonListContractionContext(
        parent      = context,
        contraction = contraction
    )

    return generateContractionCode(
        contraction = contraction,
        context     = contraction_context
    )

def generateSetContractionCode( contraction, context ):
    # Have a separate context to create list contraction code.
    contraction_context = Contexts.PythonSetContractionContext(
        parent      = context,
        contraction = contraction
    )

    return generateContractionCode(
        contraction = contraction,
        context     = contraction_context
    )

def generateDictContractionCode( contraction, context ):
    # Have a separate context to create list contraction code.
    contraction_context = Contexts.PythonDictContractionContext(
        parent      = context,
        contraction = contraction
    )

    return generateContractionCode(
        contraction = contraction,
        context     = contraction_context
    )

def generateGeneratorExpressionCode( generator_expression, context ):
    # Have a separate context to create generator expression code.
    generator_context = Contexts.PythonGeneratorExpressionContext(
        parent      = context,
        contraction = generator_expression
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

def _generateDefaultIdentifiers( parameters, default_expressions, sub_context, context ):
    default_access_identifiers = []
    default_value_identifiers = []

    assert len( default_expressions ) == len( parameters.getDefaultParameterVariables() )

    for default_parameter_value, variable in zip( default_expressions, parameters.getDefaultParameterVariables() ):
        if default_parameter_value.isExpressionConstantRef() and not default_parameter_value.isMutable():
            default_access_identifiers.append(
                generateExpressionCode(
                    expression = default_parameter_value,
                    context    = sub_context
                )
            )
        else:
            default_value_identifiers.append(
                generateExpressionCode(
                    expression = default_parameter_value,
                    context    = context
                )
            )

            default_access_identifiers.append(
                Generator.getDefaultValueAccess( variable )
            )

    return default_access_identifiers, default_value_identifiers

def generateLambdaCode( lambda_expression, context ):
    assert lambda_expression.isExpressionLambdaBuilder()

    function_context, function_codes = generateFunctionBodyCode(
        function = lambda_expression.getBody(),
        context  = context
    )

    parameters = lambda_expression.getParameters()

    default_access_identifiers, default_value_identifiers = _generateDefaultIdentifiers(
        parameters          = parameters,
        default_expressions = lambda_expression.getDefaultExpressions(),
        sub_context         = function_context,
        context             = context
    )

    lambda_decl = Generator.getFunctionDecl(
        function_identifier = lambda_expression.getCodeName(),
        decorator_count     = 0,
        default_identifiers = default_access_identifiers,
        closure_variables   = lambda_expression.getClosureVariables(),
        is_genexpr          = False,
        context             = context
    )

    if lambda_expression.isGenerator():
        lambda_code = Generator.getGeneratorFunctionCode(
            context                    = function_context,
            function_name              = "<lambda>",
            function_identifier        = lambda_expression.getCodeName(),
            parameters                 = parameters,
            user_variables             = lambda_expression.getBody().getUserLocalVariables(),
            decorator_count            = 0, # Lambda expressions can't be decorated.
            closure_variables          = lambda_expression.getClosureVariables(),
            default_access_identifiers = default_access_identifiers,
            function_codes             = function_codes,
            function_filename          = lambda_expression.getParentModule().getFilename(),
            function_doc               = None # Lambda expressions don't have doc strings
        )
    else:
        lambda_code = Generator.getFunctionCode(
            context                    = function_context,
            function_name              = "<lambda>",
            function_identifier        = lambda_expression.getCodeName(),
            parameters                 = parameters,
            user_variables             = lambda_expression.getBody().getUserLocalVariables(),
            decorator_count            = 0, # Lambda expressions can't be decorated.
            closure_variables          = lambda_expression.getClosureVariables(),
            default_access_identifiers = default_access_identifiers,
            function_codes             = function_codes,
            function_filename          = lambda_expression.getParentModule().getFilename(),
            function_doc               = None # Lambda expressions don't have doc strings
        )

    context.addFunctionCodes(
        code_name     = lambda_expression.getCodeName(),
        function_decl = lambda_decl,
        function_code = lambda_code
    )

    return Generator.getFunctionCreationCode(
        function_identifier = lambda_expression.getCodeName(),
        decorators          = (),  # Lambda expressions can't be decorated.
        default_identifiers = default_value_identifiers,
        closure_variables   = lambda_expression.getClosureVariables(),
        context             = context
    )

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
    assert function.isStatementFunctionBuilder()

    function_context, function_codes = generateFunctionBodyCode(
        function = function.getBody(),
        context  = context
    )

    parameters = function.getParameters()

    default_access_identifiers, default_value_identifiers = _generateDefaultIdentifiers(
        parameters          = parameters,
        default_expressions = function.getDefaultExpressions(),
        sub_context         = function_context,
        context             = context
    )

    if function.isGenerator():
        function_code = Generator.getGeneratorFunctionCode(
            context                    = function_context,
            function_name              = function.getFunctionName(),
            function_identifier        = function.getCodeName(),
            parameters                 = parameters,
            closure_variables          = function.getClosureVariables(),
            user_variables             = function.getBody().getUserLocalVariables(),
            decorator_count            = len( function.getDecorators() ),
            default_access_identifiers = default_access_identifiers,
            function_filename          = function.getParentModule().getFilename(),
            function_codes             = function_codes,
            function_doc               = function.getBody().getDoc()
        )
    else:
        function_code = Generator.getFunctionCode(
            context                    = function_context,
            function_name              = function.getFunctionName(),
            function_identifier        = function.getCodeName(),
            parameters                 = parameters,
            closure_variables          = function.getClosureVariables(),
            user_variables             = function.getBody().getUserLocalVariables(),
            decorator_count            = len( function.getDecorators() ),
            default_access_identifiers = default_access_identifiers,
            function_filename          = function.getParentModule().getFilename(),
            function_codes             = function_codes,
            function_doc               = function.getBody().getDoc()
        )

    function_decl = Generator.getFunctionDecl(
        function_identifier = function.getCodeName(),
        decorator_count     = len( function.getDecorators() ),
        default_identifiers = default_access_identifiers,
        closure_variables   = function.getClosureVariables(),
        is_genexpr          = False,
        context             = context

    )

    context.addFunctionCodes(
        code_name     = function.getCodeName(),
        function_decl = function_decl,
        function_code = function_code
    )

    decorators = generateExpressionsCode(
        expressions = function.getDecorators(),
        context     = context
    )

    function_creation_identifier = Generator.getFunctionCreationCode(
        function_identifier = function.getCodeName(),
        decorators          = decorators,
        default_identifiers = default_value_identifiers,
        closure_variables   = function.getClosureVariables(),
        context             = context
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
    assert class_def.isStatementClassBuilder()

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
        class_identifier  = class_def.getCodeName(),
        closure_variables = class_def.getClosureVariables(),
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
        decorators       = decorators,
        context          = context
    )

    class_decl = Generator.getClassDecl(
        class_identifier  = class_def.getCodeName(),
        closure_variables = class_def.getClosureVariables(),
        decorator_count   = len( decorators ),
        context           = context
    )

    class_code = Generator.getClassCode(
        context            = class_context,
        class_identifier   = class_def.getCodeName(),
        class_def          = class_def,
        class_name         = class_def.getClassName(),
        class_variables    = class_def.getClassVariables(),
        closure_variables  = class_def.getClosureVariables(),
        decorator_count    = len( decorators ),
        module_name        = class_def.getParentModule().getName(),
        class_filename     = class_def.getParentModule().getFilename(),
        class_doc          = class_def.getBody().getDoc(),
        class_codes        = class_codes,
        metaclass_variable = class_def.getParentModule().getVariableForReference(
            variable_name = "__metaclass__"
        )
    )

    context.addClassCodes(
        code_name  = class_def.getCodeName(),
        class_decl = class_decl,
        class_code = class_code
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

def generateDictionaryCreationCode( pairs, context ):
    keys = []
    values = []

    for pair in pairs:
        keys.append( pair.getKey() )
        values.append( pair.getValue() )

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
            context = context,
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
        if not expression.isExpressionConstantRef():
            return False

        if expression.isMutable():
            return False
    else:
        return True

def generateSliceRangeIdentifier( lower, upper, context ):
    def isSmallNumberConstant( node ):
        value = node.getConstant()

        if Constants.isNumberConstant( value ):
            return abs(int(value)) < 2**63-1
        else:
            return False


    if lower is None:
        lower = Generator.getMinIndexCode()
    elif lower.isExpressionConstantRef() and isSmallNumberConstant( lower ):
        lower = Generator.getIndexValueCode(
            int( lower.getConstant() )
        )
    else:
        lower = Generator.getIndexCode(
            identifier = generateExpressionCode(
                expression = lower,
                context    = context
            )
        )

    if upper is None:
        upper = Generator.getMaxIndexCode()
    elif upper.isExpressionConstantRef() and isSmallNumberConstant( upper ):
        upper = Generator.getIndexValueCode(
            int( upper.getConstant() )
        )
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

def generateFunctionCallNamedArgumentsCode( pairs, context ):
    if pairs:
        return generateDictionaryCreationCode(
            pairs      = pairs,
            context    = context
        )
    else:
        return None

def generateFunctionCallCode( function, context ):
    function_identifier = generateExpressionCode(
        expression = function.getCalledExpression(),
        context    = context
    )

    if function.getPositionalArguments():
        positional_args_identifier = generateSequenceCreationCode(
            sequence_kind = "tuple",
            elements      = function.getPositionalArguments(),
            context       = context
        )
    else:
        positional_args_identifier = None

    kw_identifier = generateFunctionCallNamedArgumentsCode(
        pairs   = function.getNamedArgumentPairs(),
        context = context
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

    return Generator.getFunctionCallCode(
        function_identifier  = function_identifier,
        argument_tuple       = positional_args_identifier,
        argument_dictionary  = kw_identifier,
        star_list_identifier = star_list_identifier,
        star_dict_identifier = star_dict_identifier,
    )

def _decideLocalsMode( provider ):
    if provider.isExpressionClassBody():
        mode = "updated"
    elif provider.isExpressionFunctionBody() and provider.isExecContaining():
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
    # This is a dispatching function with a branch per expression node type, and therefore
    # many statements even if every branch is small pylint: disable=R0912,R0915

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
        Tracing.printError( "No expression %r" % expression )

        expression.dump()
        assert False, expression

    if expression.isExpressionVariableRef():
        if expression.getVariable() is None:
            Tracing.printError( "Illegal variable reference, not resolved" )

            expression.dump()
            assert False, ( expression.getSourceReference(), expression.getVariableName() )

        identifier = Generator.getVariableHandle(
            variable = expression.getVariable(),
            context  = context
        )
    elif expression.isExpressionConstantRef():
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
    elif expression.isExpressionMakeSequence():
        identifier = generateSequenceCreationCode(
            sequence_kind = expression.getSequenceKind(),
            elements      = expression.getElements(),
            context       = context
        )
    elif expression.isExpressionMakeDict():
        identifier = generateDictionaryCreationCode(
            pairs   = expression.getPairs(),
            context = context
        )
    elif expression.isExpressionMakeSet():
        identifier = generateSetCreationCode(
            values    = expression.getValues(),
            context   = context
        )
    elif expression.isExpressionFunctionCall():
        identifier = generateFunctionCallCode(
            function = expression,
            context    = context
        )
    elif expression.isExpressionListContractionBuilder():
        identifier = generateListContractionCode(
            contraction = expression,
            context     = context
        )
    elif expression.isExpressionSetContractionBuilder():
        identifier = generateSetContractionCode(
            contraction = expression,
            context     = context
        )
    elif expression.isExpressionDictContractionBuilder():
        identifier = generateDictContractionCode(
            contraction = expression,
            context     = context
        )
    elif expression.isExpressionAttributeLookup():
        attribute_name = mangleAttributeName(
            attribute_name = expression.getAttributeName(),
            node           = expression
        )

        identifier = Generator.getAttributeLookupCode(
            attribute = context.getConstantHandle( attribute_name ),
            source    = makeExpressionCode( expression.getLookupSource() ),
        )
    elif expression.isExpressionSubscriptLookup():
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
    elif expression.isExpressionSliceLookup():
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
    elif expression.isExpressionSliceObject():
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
    elif expression.isExpressionBoolOR():
        identifier = Generator.getSelectionOrCode(
            conditions = generateExpressionsCode(
                expressions = expression.getExpressions(),
                context = context
            )
        )

    elif expression.isExpressionBoolAND():
        identifier = Generator.getSelectionAndCode(
            conditions = generateExpressionsCode(
                expressions = expression.getExpressions(),
                context = context
            )
        )
    elif expression.isExpressionBoolNOT():
        identifier = Generator.getConditionNotCode(
            condition = makeExpressionCode( expression = expression.getExpression() )
        )
    elif expression.isExpressionConditional():
        identifier = Generator.getConditionalExpressionCode(
            condition = generateConditionCode(
                condition = expression.getCondition(),
                context   = context
            ),
            codes_yes = makeExpressionCode( expression.getExpressionYes() ),
            codes_no  = makeExpressionCode( expression.getExpressionNo() )
        )
    elif expression.isExpressionBuiltinRange():
        identifier = Generator.getBuiltinRangeCode(
            low  = makeExpressionCode( expression.getLow(), allow_none = False ),
            high = makeExpressionCode( expression.getHigh(), allow_none = True ),
            step = makeExpressionCode( expression.getStep(), allow_none = True )
        )
    elif expression.isExpressionBuiltinGlobals():
        identifier = Generator.getLoadGlobalsCode(
            context = context
        )
    elif expression.isExpressionBuiltinLocals():
        identifier = generateBuiltinLocalsCode(
            locals_node = expression,
            context     = context
        )
    elif expression.isExpressionBuiltinDir():
        identifier = generateBuiltinDirCode(
            dir_node = expression,
            context  = context
        )
    elif expression.isExpressionBuiltinVars():
        identifier = Generator.getLoadVarsCode(
            identifier = makeExpressionCode( expression.getSource() )
        )
    elif expression.isExpressionBuiltinEval():
        identifier = generateEvalCode(
            context         = context,
            eval_expression = expression
        )
    elif expression.isExpressionBuiltinOpen():
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
        # TODO: Consider if TreeBuilding should indidcate it instead, might confuse normal
        # function generators and lambda generators or might have to treat them in the same
        # way.
        for_return = expression.parent.isStatementExpressionOnly() and \
                     expression.parent.parent.isStatementsSequence() and \
                     expression.parent.parent.parent.isExpressionFunctionBody() and \
                     expression.parent.parent.parent.parent.isExpressionLambdaBuilder()

        identifier = Generator.getYieldCode(
            identifier = makeExpressionCode(
                expression = expression.getExpression()
            ),
            for_return = for_return
        )
    elif expression.isExpressionBuiltinImport():
        identifier = generateImportBuiltinCode(
            expression = expression,
            context    = context
        )
    elif expression.isExpressionBuiltinChr():
        identifier = Generator.getBuiltinChrCode(
            value = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinOrd():
        identifier = Generator.getBuiltinOrdCode(
            value = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinLen():
        identifier = Generator.getBuiltinLenCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinType1():
        identifier = Generator.getBuiltinType1Code(
            value = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinType3():
        identifier = Generator.getBuiltinType3Code(
            name_identifier  = makeExpressionCode( expression.getTypeName() ),
            bases_identifier = makeExpressionCode( expression.getBases() ),
            dict_identifier  = makeExpressionCode( expression.getDict() ),
            context          = context
        )
    elif expression.isExpressionBuiltinTuple():
        identifier = Generator.getBuiltinTupleCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinList():
        identifier = Generator.getBuiltinListCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinDict():
        assert not expression.hasOnlyConstantArguments()

        identifier = Generator.getBuiltinDictCode(
            seq_identifier  = makeExpressionCode(
                expression.getPositionalArgument(),
                allow_none = True
            ),
            dict_identifier = generateFunctionCallNamedArgumentsCode(
                pairs    = expression.getNamedArgumentPairs(),
                context  = context
            )
        )
    elif expression.isExpressionBuiltinStr():
        identifier = Generator.getBuiltinStrCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinUnicode():
        identifier = Generator.getBuiltinUnicodeCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinFloat():
        identifier = Generator.getBuiltinFloatCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinBool():
        identifier = Generator.getBuiltinBoolCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinInt():
        assert expression.getValue() is not None or expression.getBase() is not None

        identifier = Generator.getBuiltinIntCode(
            identifier = makeExpressionCode( expression.getValue(), allow_none = True ),
            base       = makeExpressionCode( expression.getBase(), allow_none = True ),
            context    = context
        )
    elif expression.isExpressionBuiltinLong():
        assert expression.getValue() is not None or expression.getBase() is not None

        identifier = Generator.getBuiltinLongCode(
            identifier = makeExpressionCode( expression.getValue(), allow_none = True ),
            base       = makeExpressionCode( expression.getBase(), allow_none = True ),
            context    = context
        )
    elif expression.isExpressionRaiseException():
        identifier = Generator.getRaiseExceptionExpressionCode(
            side_effects               = generateExpressionsCode(
                expressions = expression.getSideEffects(),
                context     = context
            ),
            exception_type_identifier  = makeExpressionCode(
                expression = expression.getExceptionType()
            ),
            exception_value_identifier = makeExpressionCode(
                expression = expression.getExceptionValue(),
                allow_none = True
            ),
            exception_tb_maker         = Generator.getTracebackMakingIdentifier(
                context = context,
                line    = expression.getSourceReference().getLineNumber()
            )
        )
    elif expression.isExpressionBuiltinMakeException():
        identifier = Generator.getMakeExceptionCode(
            exception_type = expression.getExceptionName(),
            exception_args = generateExpressionsCode(
                expressions = expression.getArgs(),
                context     = context
            ),
            context        = context
        )
    elif expression.isExpressionBuiltinExceptionRef():
        identifier = Generator.getExceptionRefCode(
            exception_type = expression.getExceptionName(),
        )
    else:
        assert False, expression

    if not hasattr( identifier, "getCodeTemporaryRef" ):
        assert False, identifier

    return identifier

def _isComplexAssignmentTarget( targets ):
    if type( targets ) not in ( tuple, list ) and targets.isAssignTargetSomething():
        targets = [ targets ]

    return len( targets ) > 1 or targets[0].isAssignTargetTuple()


def generateAssignmentCode( targets, value, context, recursion = 1 ):
    # This is a dispatching function with a branch per assignment node type.
    # pylint: disable=R0912,R0914

    if type( targets ) not in ( tuple, list ) and targets.isAssignTargetSomething():
        targets = [ targets ]

    if not _isComplexAssignmentTarget( targets ):
        assign_source = value
        code = ""

        brace = False
    else:
        if value.getCheapRefCount() == 1:
            assign_source = Generator.TempVariableIdentifier( "rvalue_%d" % recursion )

            code = "PyObjectTemporary %s( %s );\n" % (
                assign_source.getCode(),
                value.getCodeExportRef()
            )
        else:
            assign_source = Generator.Identifier( "_python_rvalue_%d" % recursion, 0 )
            code = "PyObject *%s = %s;\n" % (
                assign_source.getCode(),
                value.getCodeTemporaryRef()
            )


        brace = True

    iterator_identifier = None

    for target in targets:
        if target.isAssignTargetSubscript():
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
        elif target.isAssignTargetAttribute():
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
        elif target.isAssignTargetSlice():
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
        elif target.isAssignTargetVariable():
            code += Generator.getVariableAssignmentCode(
                variable   = target.getTargetVariableRef().getVariable(),
                identifier = assign_source,
                context    = context
            )

            code += "\n"
        elif target.isAssignTargetTuple():
            elements = target.getElements()

            # Unpack if it's the first time.
            if iterator_identifier is None:
                iterator_identifier = Generator.getTupleUnpackIteratorCode( recursion )

                lvalue_identifiers = [
                    Generator.getTupleUnpackLeftValueCode(
                        recursion  = recursion,
                        count      = count+1,
                        # TODO: Should check for tuple assignments, this is a bit
                        # too easy
                        single_use = len( targets ) == 1
                    )
                    for count in
                    range( len( elements ))
                ]

                code += Generator.getUnpackTupleCode(
                    assign_source       = assign_source,
                    iterator_identifier = iterator_identifier,
                    lvalue_identifiers  = lvalue_identifiers,
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
        if target.isAssignTargetSubscript():
            code += Generator.getSubscriptDelCode(
                subscribed = makeExpressionCode( target.getSubscribed() ),
                subscript  = makeExpressionCode( target.getSubscript() )
            )
        elif target.isAssignTargetAttribute():
            attribute_name = mangleAttributeName(
                attribute_name = target.getAttributeName(),
                node           = target
            )

            code += Generator.getAttributeDelCode(
                target    = makeExpressionCode( target.getLookupSource() ),
                attribute = context.getConstantHandle( constant = attribute_name )
            )
        elif target.isAssignTargetVariable():
            code += Generator.getVariableDelCode(
                variable = target.getTargetVariableRef().getVariable(),
                context  = context
            )
        elif target.isAssignTargetTuple():
            elements = target.getElements()

            for element in elements:
                code += generateDelCode(
                    targets   = [ element ],
                    context   = context
                )

        elif target.isAssignTargetSlice():
            target_identifier, lower_identifier, upper_identifier = generateSliceAccessIdentifiers(
                sliced    = target.getLookupSource(),
                lower     = target.getLower(),
                upper     = target.getUpper(),
                context   = context
            )

            code += Generator.getSliceDelCode(
                target     = target_identifier,
                lower      = lower_identifier,
                upper      = upper_identifier
            )
        else:
            assert False, target

    return code

def generateAssignmentInplaceCode( statement, context ):
    def makeExpressionCode( expression ):
        return generateExpressionCode(
            expression = expression,
            context    = context
        )

    target = statement.getTarget()

    if target.isAssignTargetVariable():
        code = Generator.getInplaceVarAssignmentCode(
            variable   = target.getTargetVariableRef().getVariable(),
            operator   = statement.getOperator(),
            identifier = makeExpressionCode( statement.getExpression() ),
            context    = context
        )
    elif target.isAssignTargetSubscript():
        code = Generator.getInplaceSubscriptAssignmentCode(
            subscribed = makeExpressionCode(
                expression = target.getSubscribed()
            ),
            subscript  = makeExpressionCode(
                expression = target.getSubscript()
            ),
            operator   = statement.getOperator(),
            identifier = makeExpressionCode(
                expression = statement.getExpression()
            )
        )
    elif target.isAssignTargetAttribute():
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
            identifier = makeExpressionCode(
                expression = statement.getExpression()
            )
        )
    elif target.isAssignTargetSlice():
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
            identifier = makeExpressionCode(
                expression = statement.getExpression()
            )
        )
    else:
        assert False, ( "not supported for inplace assignment", target, target.getSourceReference() )

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
    handler_codes = []

    for count, handler in enumerate( statement.getExceptionHandlers() ):
        exception_identifier = generateExpressionCode(
            expression = handler.getExceptionType(),
            allow_none = True,
            context    = context
        )

        exception_target = handler.getExceptionTarget()

        if exception_target is not None:
            exception_assignment = generateAssignmentCode(
                targets    = exception_target,
                value      = Generator.getCurrentExceptionObjectCode(),
                context    = context
            )
        else:
            exception_assignment = None

        handler_code = generateStatementSequenceCode(
            statement_sequence = handler.getExceptionBranch(),
            allow_none         = True,
            context            = context
        )

        handler_codes += Generator.getTryExceptHandlerCode(
            exception_identifier = exception_identifier,
            exception_assignment = exception_assignment,
            handler_code         = handler_code,
            first_handler        = count == 0
        )

    return Generator.getTryExceptCode(
        context       = context,
        code_tried    = generateStatementSequenceCode(
            statement_sequence = statement.getBlockTry(),
            allow_none         = True,
            context            = context,
        ),
        handler_codes = handler_codes,
        else_code     = generateStatementSequenceCode(
            statement_sequence = statement.getBlockNoRaise(),
            allow_none         = True,
            context            = context
        )
    )

def generateRaiseCode( statement, context ):
    exception_type  = statement.getExceptionType()
    exception_value = statement.getExceptionValue()
    exception_tb    = statement.getExceptionTrace()

    if exception_type is None:
        return Generator.getReRaiseExceptionCode(
            local = statement.isReraiseExceptionLocal()
        )
    elif exception_value is None:
        return Generator.getRaiseExceptionCode(
            exception_type_identifier  = generateExpressionCode(
                expression = exception_type,
                context    = context
            ),
            exception_value_identifier = None,
            exception_tb_identifier    = None,
            exception_tb_maker         = Generator.getTracebackMakingIdentifier(
                context = context,
                line    = statement.getSourceReference().getLineNumber()
            )
        )
    elif exception_tb is None:
        return Generator.getRaiseExceptionCode(
            exception_type_identifier = generateExpressionCode(
                expression = exception_type,
                context    = context
            ),
            exception_value_identifier = generateExpressionCode(
                expression = exception_value,
                context    = context
            ),
            exception_tb_identifier    = None,
            exception_tb_maker         = Generator.getTracebackMakingIdentifier(
                context = context,
                line    = statement.getSourceReference().getLineNumber()
            )
        )
    else:
        return Generator.getRaiseExceptionCode(
            exception_type_identifier  = generateExpressionCode(
                expression = exception_type,
                context    = context
            ),
            exception_value_identifier = generateExpressionCode(
                expression = exception_value,
                context    = context
            ),
            exception_tb_identifier    = generateExpressionCode(
                expression = exception_tb,
                context    = context
            ),
            exception_tb_maker         = None
        )


def generateImportBuiltinCode( expression, context ):
    return Generator.getImportModuleCode(
        context     = context,
        module_name = expression.getModuleName(),
        import_name = expression.getImportName(),
        import_list = Generator.getEmptyImportListCode(),
        level       = expression.getLevel()
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

def generateImportFromLookupCode( statement, context ):
    module_temp = Generator.getImportFromModuleTempIdentifier()

    lookup_code = ""

    for object_name, target in zip( statement.getImports(), statement.getTargets() ):
        assert object_name != "*"

        attribute = context.getConstantHandle(
            constant = object_name
        )

        lookup_code += Generator.getDefineGuardedCode(
            define = "_NUITKA_EXE",
            code   = Generator.getBranchCode(
                condition = Generator.getAttributeCheckCode(
                    source    = module_temp,
                    attribute = attribute
                ),
                no_codes = (
                    Generator.getStatementCode(
                        Generator.getImportEmbeddedCode(
                            context     = context,
                            module_name = statement.getModuleName() + "." + object_name,
                            import_name = statement.getModuleName() + "." + object_name
                        )
                    ),
                ),
                yes_codes = ()
            )
        )

        lookup_code += "\n"

        lookup_code += generateAssignmentCode(
            targets = target,
            value   = Generator.getAttributeLookupCode(
                source    = module_temp,
                attribute = attribute
            ),
            context = context
        )

        lookup_code += "\n"

    return lookup_code


def generateImportFromExternalCode( statement, context ):
    lookup_code = generateImportFromLookupCode(
        statement = statement,
        context   = context
    )

    return Generator.getImportFromCode(
        module_name      = statement.getModuleName(),
        lookup_code      = lookup_code,
        import_list      = statement.getImports(),
        sub_module_names = (),
        level            = statement.getLevel(),
        context          = context
    )


def generateImportFromEmbeddedCode( statement, context ):
    lookup_code = generateImportFromLookupCode(
        statement = statement,
        context   = context
    )

    return Generator.getImportFromEmbeddedCode(
        module_name      = statement.getModuleName(),
        lookup_code      = lookup_code,
        sub_module_names = [
            sub_module.getFullName()
            for sub_module in
            statement.getSubModules()
        ],
        context          = context
    )


def generateImportStarExternalCode( statement, context ):
    return Generator.getImportFromStarCode(
        module_name = statement.getModuleName(),
        level       = statement.getLevel(),
        context     = context
    )

def generateImportStarEmbeddedCode( statement, context ):
    return Generator.getImportFromStarEmbeddedCode(
        module_name = statement.getModuleName(),
        context     = context
    )

def generatePrintCode( statement, target_file, context ):
    values = generateExpressionsCode(
        context     = context,
        expressions = statement.getValues()
    )

    return Generator.getPrintCode(
        target_file = target_file,
        identifiers = values,
        newline     = statement.isNewlinePrint()
    )

def generateBranchCode( statement, context ):
    return Generator.getBranchCode(
        condition      = generateConditionCode(
            condition = statement.getCondition(),
            context   = context
        ),
        yes_codes = generateStatementSequenceCode(
            statement_sequence = statement.getBranchYes(),
            allow_none         = True,
            context            = context
        ),
        no_codes = generateStatementSequenceCode(
            statement_sequence = statement.getBranchNo(),
            allow_none         = True,
            context            = context
        )
    )

def generateWhileLoopCode( statement, context ):
    loop_body_codes = generateStatementSequenceCode(
        statement_sequence = statement.getLoopBody(),
        allow_none         = True,
        context            = context
    )


    loop_else_codes = generateStatementSequenceCode(
        statement_sequence = statement.getNoEnter(),
        allow_none         = True,
        context            = context
    )

    return Generator.getWhileLoopCode(
        condition        = generateConditionCode(
            condition = statement.getCondition(),
            context   = context
        ),
        loop_body_codes  = loop_body_codes,
        loop_else_codes  = loop_else_codes,
        context          = context,
        needs_exceptions = statement.needsExceptionBreakContinue(),
    )

def mayRaise( targets ):
    if type( targets ) not in ( tuple, list ) and targets.isAssignTargetSomething():
        targets = [ targets ]

    # TODO: Identify more things that cannot raise. Slices, etc. could be annotated
    # in finalization if their lookup could fail at all.

    for target in targets:
        if target.isAssignTargetVariable():
            pass
        else:
            break
    else:
        return False

    return True

def generateForLoopCode( statement, context ):

    iter_name, iter_value, iter_object = Generator.getForLoopNames( context = context )

    iterator = Generator.getIteratorCreationCode(
        iterated = generateExpressionCode(
            expression = statement.getIterated(),
            context    = context
        )
    )

    targets = statement.getLoopVariableAssignment()

    if _isComplexAssignmentTarget( targets ) or mayRaise( targets ):
        iter_identifier = Generator.TempVariableIdentifier( iter_object )

        assignment_code = "PyObjectTemporary %s( %s );\n" % (
            iter_identifier.getCode(),
            iter_value
        )
    else:
        iter_identifier = Generator.Identifier( iter_value, 1 )

        assignment_code = ""

    assignment_code += generateAssignmentCode(
        targets = targets,
        value   = iter_identifier,
        context = context
    )

    loop_body_codes = generateStatementSequenceCode(
        statement_sequence = statement.getBody(),
        allow_none         = True,
        context            = context
    )


    loop_else_codes = generateStatementSequenceCode(
        statement_sequence = statement.getNoBreak(),
        allow_none         = True,
        context            = context
    )

    if Options.shallHaveStatementLines():
        line_number_code = Generator.getCurrentLineCode(
            source_ref = statement.getIterated().getSourceReference()
        )
    else:
        line_number_code = ""

    return Generator.getForLoopCode(
        line_number_code = line_number_code,
        iterator         = iterator,
        iter_name        = iter_name,
        iter_value       = iter_value,
        iter_object      = iter_identifier,
        loop_var_code    = assignment_code,
        loop_body_codes  = loop_body_codes,
        loop_else_codes  = loop_else_codes,
        needs_exceptions = statement.needsExceptionBreakContinue(),
        context          = context
    )

def generateWithCode( statement, context ):
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

    return Generator.getWithCode(
        source_identifier       = generateExpressionCode(
            expression = statement.getExpression(),
            context    = context
        ),
        assign_codes            = assign_codes,
        with_manager_identifier = with_manager_identifier,
        with_value_identifier   = with_value_identifier,
        body_codes              = body_codes,
        context                 = context
    )

def generateReturnCode( statement, context ):
    parent_function = statement.getParentFunction()

    if parent_function is not None and parent_function.isGenerator():
        return Generator.getYieldTerminatorCode()
    else:
        return Generator.getReturnCode(
            identifier = generateExpressionCode(
                expression = statement.getExpression(),
                context    = context
            )
        )

def generateStatementCode( statement, context ):
    try:
        return _generateStatementCode( statement, context )
    except:
        Tracing.printError( "Problem with %r at %s" % ( statement, statement.getSourceReference() ) )
        raise

def _generateStatementCode( statement, context ):
    # This is a dispatching function with a branch per statement node type.
    # pylint: disable=R0912,R0915

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
    elif statement.isStatementAssignmentInplace():
        code = generateAssignmentInplaceCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementFunctionBuilder():
        code = generateFunctionCode(
            function  = statement,
            context   = context
        )
    elif statement.isStatementClassBuilder():
        code = generateClassCode(
            class_def = statement,
            context   = context
        )
    elif statement.isStatementExpressionOnly():
        code = Generator.getStatementCode(
            identifier = makeExpressionCode(
                statement.getExpression()
            )
        )
    elif statement.isStatementPrint():
        code = generatePrintCode(
            statement   = statement,
            target_file = makeExpressionCode(
                expression = statement.getDestination(),
                allow_none = True
            ),
            context     = context
        )
    elif statement.isStatementReturn():
        code = generateReturnCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementWith():
        code = generateWithCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementForLoop():
        code = generateForLoopCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementWhileLoop():
        code = generateWhileLoopCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementConditional():
        code = generateBranchCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementContinueLoop():
        code = Generator.getLoopContinueCode(
            needs_exceptions = statement.needsExceptionBreakContinue()
        )
    elif statement.isStatementBreakLoop():
        code = Generator.getLoopBreakCode(
            needs_exceptions = statement.needsExceptionBreakContinue()
        )
    elif statement.isStatementImportExternal():
        code = generateImportExternalCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementImportEmbedded():
        code = generateImportEmbeddedCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementImportFromExternal():
        code = generateImportFromExternalCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementImportFromEmbedded():
        code = generateImportFromEmbeddedCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementImportStarExternal():
        code = generateImportStarExternalCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementImportStarEmbedded():
        code = generateImportStarEmbeddedCode(
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
            failure_identifier   = makeExpressionCode(
                expression = statement.getArgument(),
                allow_none = True
            ),
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

def generateStatementSequenceCode( statement_sequence, context, allow_none = False ):
    if allow_none and statement_sequence is None:
        return None

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
        assert statement_codes[-1].strip() != "", ( "Code '%s'" % code, statement )

        codes += statement_codes

    return codes

def generateModuleCode( module, module_name, global_context, stand_alone ):
    assert module.isModule(), module

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
        path_identifier = context.getConstantHandle(
            constant = module.getPathAttribute()
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

def generateModuleDeclarationCode( module_name ):
    return Generator.getModuleDeclarationCode(
        module_name = module_name
    )

def generateMainCode( codes, other_modules ):
    return Generator.getMainCode(
        codes              = codes,
        other_module_names = [ other_module.getFullName() for other_module in other_modules ]
    )

def generateConstantsDeclarationCode( context ):
    return Generator.getConstantsDeclarationCode(
        context = context
    )

def generateConstantsDefinitionCode( context ):
    return Generator.getConstantsDefinitionCode(
        context = context
    )

def generateReversionMacrosCode( context ):
    return Generator.getReversionMacrosCode(
        context = context
    )


def makeGlobalContext():
    return Contexts.PythonGlobalContext()
