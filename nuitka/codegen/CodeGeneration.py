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
    Options,
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

        if node.isExpressionFunctionBody() and node.isClassDictCreation():
            if seen_function:
                return "_" + node.getName() + attribute_name
            else:
                return attribute_name
        elif node.isExpressionFunctionBody():
            seen_function = True

    return attribute_name

def generateTupleCreationCode( elements, context ):
    if _areConstants( elements ):
        return Generator.getConstantHandle(
            context  = context,
            constant = tuple( element.getConstant() for element in elements )
        )
    else:
        identifiers = generateExpressionsCode(
            expressions = elements,
            context     = context
        )

        return Generator.getTupleCreationCode(
            element_identifiers = identifiers,
            context             = context
        )

def generateListCreationCode( elements, context ):
    if _areConstants( elements ):
        return Generator.getConstantHandle(
            context  = context,
            constant = list( element.getConstant() for element in elements )
        )
    else:
        identifiers = generateExpressionsCode(
            expressions = elements,
            context     = context
        )

        return Generator.getListCreationCode(
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
        result = generateComparisonExpressionBoolCode(
            comparison_expression = condition,
            context               = context
        )

        if inverted:
            result = Generator.getConditionNotBoolCode(
                condition = result
            )
    elif condition.isExpressionOperationBool2():
        parts = []

        for expression in condition.getOperands():
            parts.append(
                generateConditionCode(
                    condition = expression,
                    context   = context
                )
            )

        if condition.isExpressionBoolOR():
            result = Generator.getConditionOrCode( parts )
        else:
            result = Generator.getConditionAndCode( parts )

        if inverted:
            result = Generator.getConditionNotBoolCode(
                condition = result
            )
    elif condition.isExpressionOperationNOT():
        if not inverted:
            result = Generator.getConditionNotBoolCode(
                condition = generateConditionCode(
                    condition = condition.getOperand(),
                    context   = context
                )
            )
        else:
            result = generateConditionCode(
                condition = condition.getOperand(),
                context   = context
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

def generateFunctionCallCode( call_node, context ):
    assert call_node.getFunction().isExpressionFunctionCreation()

    function_body = call_node.getFunction().getFunctionBody()

    function_identifier = generateFunctionBodyCode(
        function_body  = function_body,
        defaults       = (), # TODO: Can't be right or needs check
        context        = context
    )

    extra_arguments = []

    if call_node.isExpressionClassDefinition():
        extra_arguments.append(
            generateExpressionCode(
                expression = call_node.getMetaclass(),
                allow_none = True,
                context    = context
            )
        )

        extra_arguments.append(
            generateTupleCreationCode(
                elements = call_node.getBases(),
                context  = context
            )
        )

    return Generator.getDirectionFunctionCallCode(
        function_identifier = function_identifier,
        arguments           = generateExpressionsCode(
            expressions = call_node.getArgumentValues(),
            context     = context
        ),
        closure_variables  = function_body.getClosureVariables(),
        extra_arguments    = extra_arguments,
        context            = context
    )

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

def generateFunctionBodyCode( function_body, defaults, context ):
    function_context = Contexts.PythonFunctionContext(
        parent         = context,
        function       = function_body
    )

    function_codes = generateStatementSequenceCode(
        statement_sequence = function_body.getBody(),
        allow_none         = True,
        context            = function_context
    )

    function_codes = function_codes or []

    parameters = function_body.getParameters()

    default_access_identifiers, default_value_identifiers = _generateDefaultIdentifiers(
        parameters          = parameters,
        default_expressions = defaults,
        sub_context         = function_context,
        context             = context
    )

    if function_body.isGenerator():
        function_code = Generator.getGeneratorFunctionCode(
            context                    = function_context,
            function_name              = function_body.getFunctionName(),
            function_identifier        = function_body.getCodeName(),
            parameters                 = parameters,
            closure_variables          = function_body.getClosureVariables(),
            user_variables             = function_body.getUserLocalVariables(),
            tmp_variables              = function_body.getTempKeeperNames(),
            default_access_identifiers = default_access_identifiers,
            needs_creation             = function_body.needsCreation(),
            source_ref                 = function_body.getSourceReference(),
            function_codes             = function_codes,
            function_doc               = function_body.getDoc()
        )
    else:
        function_code = Generator.getFunctionCode(
            context                    = function_context,
            function_name              = function_body.getFunctionName(),
            function_identifier        = function_body.getCodeName(),
            parameters                 = parameters,
            closure_variables          = function_body.getClosureVariables(),
            user_variables             = function_body.getUserLocalVariables(),
            tmp_variables              = function_body.getTempKeeperNames(),
            default_access_identifiers = default_access_identifiers,
            needs_creation             = function_body.needsCreation(),
            source_ref                 = function_body.getSourceReference(),
            function_codes             = function_codes,
            function_doc               = function_body.getDoc()
        )

    function_decl = Generator.getFunctionDecl(
        function_identifier          = function_body.getCodeName(),
        default_identifiers          = default_access_identifiers,
        closure_variables            = function_body.getClosureVariables(),
        function_parameter_variables = function_body.getParameters().getVariables(),
        context                      = function_context
    )

    context.addFunctionCodes(
        code_name     = function_body.getCodeName(),
        function_decl = function_decl,
        function_code = function_code
    )

    if function_body.needsCreation():
        return Generator.getFunctionCreationCode(
            function_identifier = function_body.getCodeName(),
            default_identifiers = default_value_identifiers,
            closure_variables   = function_body.getClosureVariables(),
            context             = context
        )
    else:
        return function_body.getCodeName()

def generateOperationCode( operator, operands, context ):
    return Generator.getOperationCode(
        operator    = operator,
        identifiers = generateExpressionsCode(
            expressions = operands,
            context     = context
        )
    )

def generateComparisonExpressionCode( comparison_expression, context ):
    left = generateExpressionCode(
        expression = comparison_expression.getLeft(),
        context    = context
    )
    right = generateExpressionCode(
        expression = comparison_expression.getRight(),
        context    = context
    )

    return Generator.getComparisonExpressionCode(
        comparator        = comparison_expression.getComparator(),
        left              = left,
        right             = right
    )

def generateComparisonExpressionBoolCode( comparison_expression, context ):
    left = generateExpressionCode(
        expression = comparison_expression.getLeft(),
        context    = context
    )
    right = generateExpressionCode(
        expression = comparison_expression.getRight(),
        context    = context
    )

    return Generator.getComparisonExpressionBoolCode(
        comparator        = comparison_expression.getComparator(),
        left              = left,
        right             = right
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

def generateSetCreationCode( elements, context ):
    element_identifiers = generateExpressionsCode(
        expressions = elements,
        context     = context
    )

    return Generator.getSetCreationCode(
        element_identifiers = element_identifiers,
        context             = context
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

_slicing_available = Utils.python_version < 300

def decideSlicing( lower, upper ):
    return _slicing_available and                       \
           ( lower is None or lower.isIndexable() ) and \
           ( upper is None or upper.isIndexable() )

def generateSliceLookupCode( expression, context ):
    lower = expression.getLower()
    upper = expression.getUpper()

    if decideSlicing( lower, upper ):
        expression_identifier, lower_identifier, upper_identifier = generateSliceAccessIdentifiers(
            sliced    = expression.getLookupSource(),
            lower     = lower,
            upper     = upper,
            context   = context
        )

        return Generator.getSliceLookupIndexesCode(
            source  = expression_identifier,
            lower   = lower_identifier,
            upper   = upper_identifier
        )
    else:
        if _slicing_available:
            return Generator.getSliceLookupCode(
                source  = generateExpressionCode(
                    expression = expression.getLookupSource(),
                    context    = context
                ),
                lower   = generateExpressionCode(
                    expression = lower,
                    allow_none = True,
                    context    = context
                ),
                upper   = generateExpressionCode(
                    expression = upper,
                    allow_none = True,
                    context    = context
                )
            )
        else:
            return Generator.getSubscriptLookupCode(
                source    = generateExpressionCode(
                    expression = expression.getLookupSource(),
                    context    = context
                ),
                subscript = Generator.getSliceObjectCode(
                    lower = generateExpressionCode(
                        expression = lower,
                        allow_none = True,
                        context    = context
                    ),
                    upper = generateExpressionCode(
                        expression = upper,
                        allow_none = True,
                        context    = context
                    ),
                    step    = None
                )
            )

def generateCallNamedArgumentsCode( pairs, context ):
    if pairs:
        return generateDictionaryCreationCode(
            pairs      = pairs,
            context    = context
        )
    else:
        return None

def generateCallCode( call_node, context ):
    # TODO: Misnomer
    function_identifier = generateExpressionCode(
        expression = call_node.getCalled(),
        context    = context
    )

    if call_node.getPositionalArguments():
        positional_args_identifier = generateTupleCreationCode(
            elements = call_node.getPositionalArguments(),
            context  = context
        )
    else:
        positional_args_identifier = None

    kw_identifier = generateCallNamedArgumentsCode(
        pairs   = call_node.getNamedArgumentPairs(),
        context = context
    )

    star_list_identifier = generateExpressionCode(
        expression = call_node.getStarListArg(),
        allow_none = True,
        context    = context
    )

    star_dict_identifier = generateExpressionCode(
        expression = call_node.getStarDictArg(),
        allow_none = True,
        context    = context
    )

    return Generator.getCallCode(
        function_identifier  = function_identifier,
        argument_tuple       = positional_args_identifier,
        argument_dictionary  = kw_identifier,
        star_list_identifier = star_list_identifier,
        star_dict_identifier = star_dict_identifier,
    )

def _decideLocalsMode( provider ):
    if provider.isExpressionFunctionBody() and ( provider.isEarlyClosure() or provider.isUnoptimized() ):
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

def generateBuiltinDir0Code( dir_node, context ):
    provider = dir_node.getParentVariableProvider()

    return Generator.getLoadDirCode(
        context  = context,
        provider = provider
    )

def generateBuiltinDir1Code( dir_node, context ):
    return Generator.getBuiltinDir1Code(
        identifier = generateExpressionCode(
            expression = dir_node.getValue(),
            context    = context
        )
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

        identifier = Generator.getVariableAccess(
            variable = expression.getVariable(),
            context  = context
        )
    elif expression.isExpressionTempVariableRef():
        identifier = Generator.getVariableAccess(
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
    elif expression.isExpressionMakeTuple():
        identifier = generateTupleCreationCode(
            elements = expression.getElements(),
            context  = context
        )
    elif expression.isExpressionMakeList():
        identifier = generateListCreationCode(
            elements = expression.getElements(),
            context  = context
        )
    elif expression.isExpressionMakeSet():
        identifier = generateSetCreationCode(
            elements = expression.getElements(),
            context  = context
        )
    elif expression.isExpressionMakeDict():
        identifier = generateDictionaryCreationCode(
            pairs   = expression.getPairs(),
            context = context
        )
    elif expression.isExpressionCall():
        identifier = generateCallCode(
            call_node = expression,
            context   = context
        )
    elif expression.isExpressionFunctionCall() or expression.isExpressionClassDefinition():
        identifier = generateFunctionCallCode(
            call_node = expression,
            context   = context
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
    elif expression.isExpressionSpecialAttributeLookup():
        identifier = Generator.getSpecialAttributeLookupCode(
            attribute = context.getConstantHandle( expression.getAttributeName() ),
            source    = makeExpressionCode( expression.getLookupSource() ),
        )

    elif expression.isExpressionImportName():
        identifier = Generator.getImportNameCode(
            import_name = context.getConstantHandle( expression.getImportName() ),
            module      = makeExpressionCode( expression.getModule() ),
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
        identifier = generateSliceLookupCode(
            expression = expression,
            context    = context
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
                expressions = expression.getOperands(),
                context = context
            )
        )

    elif expression.isExpressionBoolAND():
        identifier = Generator.getSelectionAndCode(
            conditions = generateExpressionsCode(
                expressions = expression.getOperands(),
                context = context
            )
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
    elif expression.isExpressionBuiltinRange1():
        identifier = Generator.getBuiltinRangeCode(
            low  = makeExpressionCode( expression.getLow() ),
            high = None,
            step = None
        )
    elif expression.isExpressionBuiltinRange2():
        identifier = Generator.getBuiltinRangeCode(
            low  = makeExpressionCode( expression.getLow() ),
            high = makeExpressionCode( expression.getHigh() ),
            step = None
        )
    elif expression.isExpressionBuiltinRange3():
        identifier = Generator.getBuiltinRangeCode(
            low  = makeExpressionCode( expression.getLow() ),
            high = makeExpressionCode( expression.getHigh() ),
            step = makeExpressionCode( expression.getStep() )
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
    elif expression.isExpressionBuiltinDir0():
        identifier = generateBuiltinDir0Code(
            dir_node = expression,
            context  = context
        )
    elif expression.isExpressionBuiltinDir1():
        identifier = generateBuiltinDir1Code(
            dir_node = expression,
            context  = context
        )
    elif expression.isExpressionBuiltinVars():
        identifier = Generator.getLoadVarsCode(
            identifier = makeExpressionCode( expression.getSource() )
        )
    elif expression.isExpressionBuiltinEval():
        identifier = generateEvalCode(
            context   = context,
            eval_node = expression
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
    elif expression.isExpressionFunctionCreation():
        identifier = generateFunctionBodyCode(
            function_body  = expression.getFunctionBody(),
            defaults       = expression.getDefaults(),
            context        = context
        )
    elif expression.isExpressionClassCreation():
        context.addGlobalVariableNameUsage( "__metaclass__" )

        identifier = Generator.getClassCreationCode(
            metaclass_global_code = Generator.getMetaclassVariableCode(
                context = context
            ),
            name_identifier       = Generator.getConstantHandle(
                context  = context,
                constant = expression.getClassName()
            ),
            dict_identifier       = makeExpressionCode(
                expression = expression.getClassDict()
            )
        )
    elif expression.isExpressionComparison():
        identifier = generateComparisonExpressionCode(
            comparison_expression = expression,
            context               = context
        )
    elif expression.isExpressionYield():
        identifier = Generator.getYieldCode(
            identifier = makeExpressionCode(
                expression = expression.getExpression()
            ),
            for_return = expression.isForReturn()
        )
    elif expression.isExpressionImportModule():
        identifier = generateImportModuleCode(
            expression = expression,
            context    = context
        )
    elif expression.isExpressionBuiltinImport():
        identifier = generateBuiltinImportCode(
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
    elif expression.isExpressionBuiltinBin():
        identifier = Generator.getBuiltinBinCode(
            value = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinOct():
        identifier = Generator.getBuiltinOctCode(
            value = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinHex():
        identifier = Generator.getBuiltinHexCode(
            value = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinLen():
        identifier = Generator.getBuiltinLenCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinIter1():
        identifier = Generator.getBuiltinIter1Code(
            value = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinIter2():
        identifier = Generator.getBuiltinIter2Code(
            callable_identifier = makeExpressionCode( expression.getCallable() ),
            sentinel_identifier = makeExpressionCode( expression.getSentinel() )
        )
    elif expression.isExpressionBuiltinNext1():
        identifier = Generator.getBuiltinNext1Code(
            value = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionSpecialUnpack():
        identifier = Generator.getUnpackNextCode(
            iterator_identifier = makeExpressionCode( expression.getValue() ),
            count               = expression.getCount()
        )
    elif expression.isExpressionBuiltinNext2():
        identifier = Generator.getBuiltinNext2Code(
            iterator_identifier = makeExpressionCode( expression.getIterator() ),
            default_identifier = makeExpressionCode( expression.getDefault() )
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
                expression = expression.getPositionalArgument(),
                allow_none = True
            ),
            dict_identifier = generateCallNamedArgumentsCode(
                pairs    = expression.getNamedArgumentPairs(),
                context  = context
            )
        )
    elif Utils.python_version < 300 and expression.isExpressionBuiltinStr():
        identifier = Generator.getBuiltinStrCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif Utils.python_version < 300 and expression.isExpressionBuiltinUnicode() or \
         Utils.python_version >= 300 and expression.isExpressionBuiltinStr():
        identifier = Generator.getBuiltinUnicodeCode(
            identifier = makeExpressionCode(
                expression = expression.getValue()
            ),
            encoding   = makeExpressionCode(
                expression = expression.getEncoding(),
                allow_none = True
            ),
            errors     = makeExpressionCode(
                expression = expression.getErrors(),
                allow_none = True
            )
        )
    elif expression.isExpressionBuiltinFloat():
        identifier = Generator.getBuiltinFloatCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinBool():
        identifier = Generator.getBuiltinBoolCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionRaiseException():
        identifier = Generator.getRaiseExceptionExpressionCode(
            exception_type_identifier  = makeExpressionCode(
                expression = expression.getExceptionType()
            ),
            exception_value_identifier = makeExpressionCode(
                expression = expression.getExceptionValue(),
                allow_none = True
            ),
            exception_tb_maker         = Generator.getTracebackMakingIdentifier(
                context = context,
            )
        )
    elif expression.isExpressionBuiltinMakeException():
        identifier = Generator.getMakeBuiltinExceptionCode(
            exception_type = expression.getExceptionName(),
            exception_args = generateExpressionsCode(
                expressions = expression.getArgs(),
                context     = context
            ),
            context        = context
        )
    elif expression.isExpressionBuiltinRef():
        identifier = Generator.getBuiltinRefCode(
            builtin_name = expression.getBuiltinName(),
            context      = context
        )
    elif expression.isExpressionBuiltinAnonymousRef():
        identifier = Generator.getBuiltinAnonymousRefCode(
            builtin_name = expression.getBuiltinName(),
        )
    elif expression.isExpressionBuiltinExceptionRef():
        identifier = Generator.getExceptionRefCode(
            exception_type = expression.getExceptionName(),
        )
    elif expression.isExpressionAssignmentTempKeeper():
        source_identifier = makeExpressionCode( expression.getAssignSource() )

        # TODO: Use assign0 too
        identifier = Generator.Identifier(
            "%s.assign1( %s )" % (
                expression.getVariableName(),
                source_identifier.getCodeExportRef()
            ),
            0
        )
    elif expression.isExpressionBuiltinInt():
        assert expression.getValue() is not None or expression.getBase() is not None

        identifier = Generator.getBuiltinIntCode(
            identifier = makeExpressionCode( expression.getValue(), allow_none = True ),
            base       = makeExpressionCode( expression.getBase(), allow_none = True ),
            context    = context
        )
    elif Utils.python_version < 300 and expression.isExpressionBuiltinLong():
        assert expression.getValue() is not None or expression.getBase() is not None

        identifier = Generator.getBuiltinLongCode(
            identifier = makeExpressionCode( expression.getValue(), allow_none = True ),
            base       = makeExpressionCode( expression.getBase(), allow_none = True ),
            context    = context
        )
    elif expression.isExpressionCaughtExceptionTypeRef():
        identifier = Generator.getCurrentExceptionTypeCode()
    elif expression.isExpressionCaughtExceptionValueRef():
        identifier = Generator.getCurrentExceptionValueCode()
    elif expression.isExpressionCaughtExceptionTracebackRef():
        identifier = Generator.getCurrentExceptionTracebackCode()
    elif expression.isExpressionListOperationAppend():
        identifier = Generator.getListOperationAppendCode(
            list_identifier  = makeExpressionCode( expression.getList() ),
            value_identifier = makeExpressionCode( expression.getValue() ),
        )
    elif expression.isExpressionSetOperationAdd():
        identifier = Generator.getSetOperationAddCode(
            set_identifier   = makeExpressionCode( expression.getSet() ),
            value_identifier = makeExpressionCode( expression.getValue() ),
        )
    elif expression.isExpressionDictOperationSet():
        identifier = Generator.getDictOperationSetCode(
            dict_identifier  = makeExpressionCode( expression.getDict() ),
            key_identifier   = makeExpressionCode( expression.getKey() ),
            value_identifier = makeExpressionCode( expression.getValue() ),
        )
    elif expression.isExpressionTempKeeperRef():
        identifier = Generator.Identifier(
            "%s.asObject()" % expression.getVariableName(),
            1
        )
    elif expression.isExpressionSideEffects():
        identifier = Generator.getSideEffectsCode(
            side_effects = generateExpressionsCode(
                expressions = expression.getSideEffects(),
                context     = context
            ),
            identifier   = makeExpressionCode( expression.getExpression() )
        )
    elif expression.isExpressionBuiltinSuper():
        type_identifier = makeExpressionCode( expression.getType(), allow_none = True )

        if type_identifier is None:
            type_identifier = None

        object_identifier = makeExpressionCode( expression.getObject(), allow_none = True )


        identifier = Generator.getBuiltinSuperCode(
            type_identifier   = type_identifier,
            object_identifier = object_identifier
        )
    elif Utils.python_version < 300 and expression.isExpressionBuiltinExecfile():
        identifier = generateExecfileCode(
            context       = context,
            execfile_node = expression
        )
    elif Utils.python_version >= 300 and expression.isExpressionBuiltinExec():
        # exec builtin of Python3, as opposed to Python2 statement
        identifier = generateEvalCode(
            context   = context,
            eval_node = expression
        )
    else:
        assert False, expression

    if not hasattr( identifier, "getCodeTemporaryRef" ):
        raise AssertionError( "not a code object?", repr( identifier ) )

    return identifier


def generateAssignmentVariableCode( variable_ref, value, context ):
    return Generator.getVariableAssignmentCode(
        variable   = variable_ref.getVariable(),
        identifier = value,
        context    = context
    )

def generateAssignmentAttributeCode( lookup_source, attribute_name, value, context ):
    return Generator.getAttributeAssignmentCode(
        target     = lookup_source,
        attribute  = context.getConstantHandle(
            constant = attribute_name
        ),
        identifier = value
    )

def generateAssignmentSubscriptCode( subscribed, subscript, value ):
    return Generator.getSubscriptAssignmentCode(
        subscribed    = subscribed,
        subscript     = subscript,
        identifier    = value
    )

def generateAssignmentSliceCode( lookup_source, lower, upper, value, context ):
    if decideSlicing( lower, upper ):
        expression_identifier, lower_identifier, upper_identifier = generateSliceAccessIdentifiers(
            sliced    = lookup_source,
            lower     = lower,
            upper     = upper,
            context   = context
        )

        return Generator.getSliceAssignmentIndexesCode(
            target     = expression_identifier,
            upper      = upper_identifier,
            lower      = lower_identifier,
            identifier = value
        )
    else:
        if _slicing_available:
            return Generator.getSliceAssignmentCode(
                target     = generateExpressionCode(
                    expression = lookup_source,
                    context    = context
                ),
                lower      = generateExpressionCode(
                    expression = lower,
                    allow_none = True,
                    context    = context
                ),
                upper      = generateExpressionCode(
                    expression = upper,
                    allow_none = True,
                    context    = context
                ),
                identifier = value
            )
        else:
            return Generator.getSubscriptAssignmentCode(
                subscribed = generateExpressionCode(
                    expression = lookup_source,
                    context    = context
                ),
                subscript  = Generator.getSliceObjectCode(
                    lower  = generateExpressionCode(
                        expression = lower,
                        allow_none = True,
                        context    = context
                    ),
                    upper  = generateExpressionCode(
                        expression = upper,
                        allow_none = True,
                        context    = context
                    ),
                    step   = None
                ),
                identifier = value
            )




def generateDelVariableCode( variable_ref, context ):
    return Generator.getVariableDelCode(
        variable = variable_ref.getVariable(),
        context  = context
    )

def generateDelSubscriptCode( subscribed, subscript ):
    return Generator.getSubscriptDelCode(
        subscribed = subscribed,
        subscript  = subscript
    )

def generateDelSliceCode( lookup_source, lower, upper, context ):
    if decideSlicing( lower, upper ):
        target_identifier, lower_identifier, upper_identifier = generateSliceAccessIdentifiers(
            sliced    = lookup_source,
            lower     = lower,
            upper     = upper,
            context   = context
        )

        return Generator.getSliceDelCode(
            target = target_identifier,
            lower  = lower_identifier,
            upper  = upper_identifier
        )
    else:
        return Generator.getSubscriptDelCode(
            subscribed  = generateExpressionCode(
                expression = lookup_source,
                context    = context
            ),
            subscript = Generator.getSliceObjectCode(
                lower = generateExpressionCode(
                    expression = lower,
                    allow_none = True,
                    context    = context
                ),
                upper = generateExpressionCode(
                    expression = upper,
                    allow_none = True,
                    context    = context
                ),
                step    = None
            ),
        )

def generateDelAttributeCode( statement, context ):
    attribute_name = mangleAttributeName(
        attribute_name = statement.getAttributeName(),
        node           = statement
    )
    return Generator.getAttributeDelCode(
        target    = generateExpressionCode(
            expression = statement.getLookupSource(),
            context    = context
        ),
        attribute = context.getConstantHandle(
            constant = attribute_name
        )
    )

def _generateEvalCode( node, context ):
    globals_value = node.getGlobals()

    if globals_value is None:
        globals_identifier = Generator.getConstantHandle(
            constant = None,
            context  = context
        )
    else:
        globals_identifier = generateExpressionCode(
            expression = globals_value,
            context    = context
        )

    locals_value = node.getLocals()

    if locals_value is None:
        locals_identifier = Generator.getConstantHandle(
            constant = None,
            context  = context
        )
    else:
        locals_identifier = generateExpressionCode(
            expression = locals_value,
            context    = context
        )

    if node.isExpressionBuiltinEval() or \
         ( Utils.python_version >= 300 and node.isExpressionBuiltinExec() ):
        filename = "<string>"
    else:
        filename = "<execfile>"

    identifier = Generator.getEvalCode(
        exec_code           = generateExpressionCode(
            expression = node.getSourceCode(),
            context    = context
        ),
        globals_identifier  = globals_identifier,
        locals_identifier   = locals_identifier,
        filename_identifier = Generator.getConstantCode(
            constant = filename,
            context  = context
        ),
        mode_identifier    = Generator.getConstantCode(
            constant = "eval" if node.isExpressionBuiltinEval() else "exec",
            context  = context
        ),
        future_flags        = Generator.getFutureFlagsCode(
            future_spec = node.getSourceReference().getFutureSpec()
        ),
        provider            = node.getParentVariableProvider(),
        context             = context
    )

    return identifier

def generateEvalCode( eval_node, context ):
    return _generateEvalCode(
        node    = eval_node,
        context = context
    )

def generateExecfileCode( execfile_node, context ):
    return _generateEvalCode(
        node    = execfile_node,
        context = context
    )

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
    tried_block = statement.getBlockTry()

    assert tried_block.mayRaiseException( BaseException )

    # Try to find "simple code" cases. TODO: this should be more general, but that's what
    # is needed immediately.
    tried_statements = tried_block.getStatements()

    if len( tried_statements ) == 1:
        tried_statement = tried_statements[0]

        if tried_statement.isStatementAssignmentVariable():
            source = tried_statement.getAssignSource()

            if source.isExpressionBuiltinNext1():
                if not source.getValue().mayRaiseException( BaseException ):
                    # Note: Now we know the source lookup is the only thing that may
                    # raise.

                    handlers = statement.getExceptionHandlers()

                    if len( handlers ) == 1:
                        catched_types = handlers[0].getExceptionTypes()

                        if len( catched_types ) == 1:
                            catched_type = catched_types[0]
                            if catched_type.isExpressionBuiltinExceptionRef():
                                if catched_type.getExceptionName() == "StopIteration":
                                    if handlers[0].getExceptionBranch().isStatementAbortative():

                                        temp_number = context.allocateForLoopNumber()

                                        return """\
PyObject *_tmp_unpack_%(tmp_count)d = ITERATOR_NEXT( %(source_identifier)s );

if ( _tmp_unpack_%(tmp_count)d == NULL )
{
%(handler_code)s
}
%(assignment_code)s""" % {
    "tmp_count" : temp_number,
    "handler_code" : Generator.indented( generateStatementSequenceCode(
        statement_sequence = handlers[0].getExceptionBranch(),
        allow_none         = True,
        context            = context
     ) ),
     "assignment_code" : generateAssignmentVariableCode(
        variable_ref = tried_statement.getTargetVariableRef(),
        value        = Generator.Identifier( "_tmp_unpack_%d" % temp_number, 1 ),
        context      = context
     ),
     "source_identifier" : generateExpressionCode(
        expression = source.getValue(),
        context    = context
     ).getCodeTemporaryRef()
}

    handler_codes = []

    for count, handler in enumerate( statement.getExceptionHandlers() ):
        exception_identifiers = generateExpressionsCode(
            expressions = handler.getExceptionTypes(),
            allow_none  = True,
            context     = context
        )

        handler_code = generateStatementSequenceCode(
            statement_sequence = handler.getExceptionBranch(),
            allow_none         = True,
            context            = context
        )

        handler_codes += Generator.getTryExceptHandlerCode(
            exception_identifiers = exception_identifiers,
            handler_code          = handler_code,
            first_handler         = count == 0
        )

    return Generator.getTryExceptCode(
        context       = context,
        code_tried    = generateStatementSequenceCode(
            statement_sequence = tried_block,
            context            = context,
        ),
        handler_codes = handler_codes
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

def generateImportModuleCode( expression, context ):
    provider = expression.getParentVariableProvider()

    globals_dict = Generator.getLoadGlobalsCode(
        context = context
    )

    if provider.isModule():
        locals_dict = globals_dict
    else:
        locals_dict  = generateBuiltinLocalsCode(
            locals_node = expression,
            context     = context
        )

    return Generator.getBuiltinImportCode(
        module_identifier  = Generator.getConstantHandle(
            constant = expression.getModuleName(),
            context  = context
        ),
        globals_dict       = globals_dict,
        locals_dict        = locals_dict,
        import_list        = Generator.getConstantHandle(
            constant = expression.getImportList(),
            context  = context
        ),
        level              = Generator.getConstantHandle(
            constant = expression.getLevel(),
            context  = context
        )
    )

def generateBuiltinImportCode( expression, context ):
    globals_dict = generateExpressionCode(
        expression = expression.getGlobals(),
        allow_none = True,
        context    = context
    )

    if globals_dict is None:
        globals_dict = Generator.getLoadGlobalsCode(
            context = context
        )

    locals_dict = generateExpressionCode(
        expression = expression.getLocals(),
        allow_none = True,
        context    = context
    )

    if locals_dict is None:
        provider = expression.getParentVariableProvider()

        if provider.isModule():
            locals_dict = globals_dict
        else:
            locals_dict  = generateBuiltinLocalsCode(
                locals_node = expression,
                context     = context
            )

    return Generator.getBuiltinImportCode(
        module_identifier = generateExpressionCode(
            expression = expression.getImportName(),
            context    = context
        ),
        import_list       = generateExpressionCode(
            expression = expression.getFromList(),
            context    = context
        ),
        globals_dict      = globals_dict,
        locals_dict       = locals_dict,
        level             = generateExpressionCode(
            expression = expression.getLevel(),
            context    = context
        )
    )


def generateImportStarCode( statement, context ):
    return Generator.getImportFromStarCode(
        module_identifier = generateImportModuleCode(
            expression = statement.getModule(),
            context    = context
        ),
        context     = context
    )

def generatePrintCode( statement, target_file, context ):
    expressions = statement.getValues()

    values = generateExpressionsCode(
        context     = context,
        expressions = expressions,
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

def generateLoopCode( statement, context ):
    loop_body_codes = generateStatementSequenceCode(
        statement_sequence = statement.getLoopBody(),
        allow_none         = True,
        context            = context
    )

    return Generator.getLoopCode(
        loop_body_codes  = loop_body_codes,
        needs_exceptions = statement.needsExceptionBreakContinue(),
    )

def generateTempBlock( statement, context ):
    body_codes = generateStatementSequenceCode(
        statement_sequence = statement.getBody(),
        context            = context
    )

    return Generator.getBlockCode(
        body_codes
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

    if statement.isStatementAssignmentVariable():
        code = generateAssignmentVariableCode(
            variable_ref  = statement.getTargetVariableRef(),
            value         = makeExpressionCode( statement.getAssignSource() ),
            context       = context
        )
    elif statement.isStatementAssignmentAttribute():
        code = generateAssignmentAttributeCode(
            lookup_source  = makeExpressionCode( statement.getLookupSource() ),
            attribute_name = mangleAttributeName(
                attribute_name = statement.getAttributeName(),
                node           = statement
            ),
            value          = makeExpressionCode( statement.getAssignSource() ),
            context        = context
        )
    elif statement.isStatementAssignmentSubscript():
        code = generateAssignmentSubscriptCode(
            subscribed     = makeExpressionCode( statement.getSubscribed() ),
            subscript      = makeExpressionCode( statement.getSubscript() ),
            value          = makeExpressionCode( statement.getAssignSource() ),
        )
    elif statement.isStatementAssignmentSlice():
        code = generateAssignmentSliceCode(
            lookup_source  = statement.getLookupSource(),
            lower          = statement.getLower(),
            upper          = statement.getUpper(),
            value          = makeExpressionCode( statement.getAssignSource() ),
            context        = context
        )
    elif statement.isStatementDelVariable():
        code = generateDelVariableCode(
            variable_ref = statement.getTargetVariableRef(),
            context      = context
        )
    elif statement.isStatementDelSubscript():
        code = generateDelSubscriptCode(
            subscribed = makeExpressionCode( statement.getSubscribed() ),
            subscript  = makeExpressionCode( statement.getSubscript() )
        )
    elif statement.isStatementDelSlice():
        code = generateDelSliceCode(
            lookup_source = statement.getLookupSource(),
            lower         = statement.getLower(),
            upper         = statement.getUpper(),
            context       = context
        )
    elif statement.isStatementDelAttribute():
        code = generateDelAttributeCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementTempBlock():
        code = generateTempBlock(
            statement = statement,
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
    elif statement.isStatementLoop():
        code = generateLoopCode(
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
    elif statement.isStatementImportStar():
        code = generateImportStarCode(
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
    elif statement.isStatementSpecialUnpackCheck():
        code = Generator.getUnpackCheckCode(
            iterator_identifier = makeExpressionCode( statement.getIterator() ),
            count               = statement.getCount()
        )
    else:
        assert False, statement.__class__

    if code != code.strip():
        raise AssertionError( "Code contains leading or trailing whitespace", statement, "'%s'" % code )

    return code

def generateStatementSequenceCode( statement_sequence, context, allow_none = False ):
    if allow_none and statement_sequence is None:
        return None

    assert statement_sequence.isStatementsSequence(), statement_sequence

    statements = statement_sequence.getStatements()

    codes = []

    last_ref = None

    for statement in statements:
        source_ref = statement.getSourceReference()

        if Options.shallTraceExecution():
            codes.append(
                Generator.getStatementTrace(
                    source_ref.getAsString(),
                    repr( statement )
                )
            )

        if statement.isStatementsSequence():
            code = "\n".join(
                generateStatementSequenceCode(
                    statement_sequence = statement,
                    context            = context
                )
            )

            code = code.strip()
        else:
            code = generateStatementCode(
                statement = statement,
                context   = context
            )

        # Can happen for "global" declarations, these are still in the node tree and yield
        # no code.
        if code == "":
            continue

        if source_ref != last_ref and statement.mayRaiseException( BaseException ):
            code = Generator.getLineNumberCode(
                context    = context,
                source_ref = source_ref
            ) + code

            last_ref = source_ref

        statement_codes = code.split( "\n" )

        assert statement_codes[0].strip() != "", ( "Code '%s'" % code, statement )
        assert statement_codes[-1].strip() != "", ( "Code '%s'" % code, statement )

        codes += statement_codes

    if statement_sequence.isStatementsFrame():
        provider = statement_sequence.getParentVariableProvider()
        source_ref = statement_sequence.getSourceReference()

        if provider.isExpressionFunctionBody():
            # TODO: Finalization should say this

            if provider.isGenerator():
                code = Generator.getFrameGuardLightCode(
                    frame_identifier = provider.getCodeName(),
                    code_identifier  = context.getCodeObjectHandle(
                        filename     = source_ref.getFilename(),
                        arg_names    = statement_sequence.getArgNames(),
                        line_number  = source_ref.getLineNumber(),
                        code_name    = statement_sequence.getCodeObjectName(),
                        is_generator = True
                    ),
                    codes            = codes,
                    context          = context
                )
            elif provider.code_prefix == "listcontr":
                code = Generator.getFrameGuardVeryLightCode(
                    codes = codes,
                )
            else:
                code = Generator.getFrameGuardHeavyCode(
                    frame_identifier = provider.getCodeName(),
                    code_identifier  = context.getCodeObjectHandle(
                        filename     = source_ref.getFilename(),
                        arg_names    = statement_sequence.getArgNames(),
                        line_number  = source_ref.getLineNumber(),
                        code_name    = statement_sequence.getCodeObjectName(),
                        is_generator = False,
                    ),
                    is_class         = provider.isExpressionFunctionBody() and provider.isClassDictCreation(),
                    codes            = codes,
                    context          = context
                )
        else:
            assert False, provider

        codes = code.split( "\n" )

    assert type( codes ) is list, type( codes )

    return codes

def generateModuleCode( global_context, module, module_name, other_modules ):
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
        allow_none         = True,
        context            = context,
    )

    codes = codes or []

    if module.isPackage():
        path_identifier = context.getConstantHandle(
            constant = module.getPathAttribute()
        )
    else:
        path_identifier = None

    return Generator.getModuleCode(
        module_name        = module_name,
        package_name       = module.getPackage(),
        doc_identifier     = context.getConstantHandle(
            constant = module.getDoc()
        ),
        source_ref         = module.getSourceReference(),
        path_identifier    = path_identifier,
        codes              = codes,
        tmp_variables      = module.getTempKeeperNames(),
        other_module_names = [
            other_module.getFullName()
            for other_module in
            other_modules
        ],
        context             = context,
    )

def generateModuleDeclarationCode( module_name ):
    return Generator.getModuleDeclarationCode(
        module_name = module_name
    )

def generateMainCode( context, codes ):
    return Generator.getMainCode(
        context = context,
        codes   = codes
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

def generateMakeTuplesCode( context ):
    return Generator.getMakeTuplesCode(
        context = context
    )

def generateMakeListsCode( context ):
    return Generator.getMakeListsCode(
        context = context
    )

def generateMakeDictsCode( context ):
    return Generator.getMakeDictsCode(
        context = context
    )

def generateHelpersCode( context ):
    return generateReversionMacrosCode( context ) + generateMakeTuplesCode( context ) + \
           generateMakeListsCode( context ) + generateMakeDictsCode( context )

def makeGlobalContext():
    return Contexts.PythonGlobalContext()
