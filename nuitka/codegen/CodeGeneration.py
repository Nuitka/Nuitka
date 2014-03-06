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
""" The code generation.

No language specifics at all are supposed to be present here. Instead it is
using primitives from the given generator to build either Identifiers
(referenced counted expressions) or code sequences (list of strings).

As such this is the place that knows how to take a condition and two code
branches and make a code block out of it. But it doesn't contain any target
language syntax.
"""

from . import (
    Generator,
    Contexts,
)

from nuitka import (
    PythonOperators,
    Constants,
    Tracing,
    Options,
    Utils
)

from nuitka.__past__ import iterItems

def generateTupleCreationCode(elements, context):
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
            order_relevance     = getOrderRelevance( elements ),
            context             = context
        )

def generateListCreationCode(elements, context):
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
            order_relevance     = getOrderRelevance( elements ),
            context             = context
        )

def generateConditionCode( condition, context, inverted = False,
                           allow_none = False ):
    # The complexity is needed to avoid unnecessary complex generated C++, so
    # e.g. inverted is typically a branch inside every optimizable case.
    # pylint: disable=R0912,R0915

    if condition is None and allow_none:
        assert not inverted

        result = Generator.getTrueExpressionCode()
    elif condition.isExpressionConstantRef():
        value = condition.getConstant()

        if inverted:
            value = not value
            inverted = False

        if value:
            result = Generator.getTrueExpressionCode()
        else:
            result = Generator.getFalseExpressionCode()
    elif condition.isExpressionComparison():
        left = generateExpressionCode(
            expression = condition.getLeft(),
            context    = context
        )
        right = generateExpressionCode(
            expression = condition.getRight(),
            context    = context
        )

        comparator = condition.getComparator()

        # Do not allow this, expected to be optimized away.
        assert not inverted or \
              comparator not in PythonOperators.comparison_inversions, \
                 condition

        result = Generator.getComparisonExpressionBoolCode(
            order_relevance = getOrderRelevance(
                condition.getVisitableNodes(),
            ),
            comparator      = comparator,
            left            = left,
            right           = right,
            context         = context
        )

        if inverted:
            result = Generator.getConditionNotBoolCode(
                condition = result
            )

            inverted = False
    elif condition.isExpressionOperationNOT():
        if not inverted:
            result = Generator.getConditionNotBoolCode(
                condition = generateConditionCode(
                    condition = condition.getOperand(),
                    context   = context
                )
            )

            inverted = False
        else:
            result = generateConditionCode(
                condition = condition.getOperand(),
                context   = context
            )
    elif condition.isExpressionConditional():
        expression_yes = condition.getExpressionYes()
        expression_no = condition.getExpressionNo()

        condition = condition.getCondition()

        if condition.isExpressionAssignmentTempKeeper():
            if expression_yes.isExpressionTempKeeperRef() and \
               expression_yes.getVariableName() == condition.getVariableName():
                result = Generator.getConditionOrCode(
                    operands = (
                        generateConditionCode(
                            condition = condition.getAssignSource(),
                            context   = context,
                        ),
                        generateConditionCode(
                            condition = expression_no,
                            context   = context,
                        )
                    )
                )
            elif expression_no.isExpressionTempKeeperRef() and \
               expression_no.getVariableName() == condition.getVariableName():
                result = Generator.getConditionAndCode(
                    operands = (
                        generateConditionCode(
                            condition = condition.getAssignSource(),
                            context   = context,
                        ),
                        generateConditionCode(
                            condition = expression_yes,
                            context   = context,
                        )
                    )
                )
            else:
                assert False, condition
        else:
            result = Generator.getConditionSelectionCode(
                condition_code = generateConditionCode(
                    condition = condition,
                    context   = context
                ),
                yes_code       = generateConditionCode(
                    condition = expression_yes,
                    context   = context
                ),
                no_code        = generateConditionCode(
                    condition = expression_no,
                    context   = context
                )
            )
    elif condition.isExpressionBuiltinHasattr():
        result = Generator.getAttributeCheckBoolCode(
            order_relevance = getOrderRelevance(
                condition.getVisitableNodes()
            ),
            attribute       = generateExpressionCode(
                expression = condition.getAttribute(),
                context    = context
            ),
            source          = generateExpressionCode(
                expression = condition.getLookupSource(),
                context    = context
            ),
            context         = context
        )
    elif condition.isExpressionBuiltinIsinstance():
        result = Generator.getBuiltinIsinstanceBoolCode(
            order_relevance = getOrderRelevance(
                condition.getVisitableNodes(),
            ),
            inst_identifier = generateExpressionCode(
                expression = condition.getInstance(),
                context    = context
            ),
            cls_identifier  = generateExpressionCode(
                expression = condition.getCls(),
                context    = context
            ),
            context         = context
        )
    else:
        condition_identifier = generateExpressionCode(
            expression = condition,
            context    = context
        )

        if inverted:
            result = Generator.getConditionCheckFalseCode(
                condition = condition_identifier
            )

            inverted = False
        else:
            result = Generator.getConditionCheckTrueCode(
                condition = condition_identifier
            )

    if inverted:
        result = Generator.getConditionNotBoolCode(
            condition = result
        )

    assert type(result) is str, result

    return result

def generateFunctionCallCode(call_node, context):
    assert call_node.getFunction().isExpressionFunctionCreation()

    function_body = call_node.getFunction().getFunctionRef().getFunctionBody()

    function_identifier = function_body.getCodeName()

    extra_arguments = []

    argument_values = call_node.getArgumentValues()

    return Generator.getDirectionFunctionCallCode(
        function_identifier = function_identifier,
        arguments           = generateExpressionsCode(
            expressions = argument_values,
            context     = context
        ),
        order_relevance     = getOrderRelevance( argument_values ),
        closure_variables   = function_body.getClosureVariables(),
        extra_arguments     = extra_arguments,
        context             = context
    )

_generated_functions = {}

def generateFunctionCreationCode( function_body, defaults, kw_defaults,
                                  annotations, context ):
    assert function_body.needsCreation(), function_body

    parameters = function_body.getParameters()

    if defaults:
        defaults_identifier = generateTupleCreationCode(
            elements = defaults,
            context  = context
        )
    else:
        defaults_identifier = Generator.getConstantHandle(
            constant = None,
            context  = context
        )

    if kw_defaults:
        kw_defaults_identifier = generateExpressionCode(
            expression = kw_defaults,
            context    = context
        )
    else:
        kw_defaults_identifier = Generator.getConstantHandle(
            constant = None,
            context  = context
        )

    annotations_identifier = generateExpressionCode(
        expression = annotations,
        allow_none = True,
        context    = context,
    )

    default_args = []
    order_relevance = []

    if not kw_defaults_identifier.isConstantIdentifier():
        default_args.append(kw_defaults_identifier)
        order_relevance.extend(
            getOrderRelevance( ( kw_defaults, ) )
        )

    if not defaults_identifier.isConstantIdentifier():
        default_args.append(defaults_identifier)

        order_relevance.append(
            Generator.pickFirst( getOrderRelevance( defaults ) )
        )

    if annotations_identifier is not None and \
       not annotations_identifier.isConstantIdentifier():
        default_args.append(annotations_identifier)

        order_relevance.extend(
            getOrderRelevance( ( annotations, ) )
        )

    function_identifier = function_body.getCodeName()

    maker_code = Generator.getFunctionMakerCode(
        context                = context,
        function_name          = function_body.getFunctionName(),
        function_qualname      = function_body.getFunctionQualname(),
        function_identifier    = function_identifier,
        parameters             = parameters,
        local_variables        = function_body.getLocalVariables(),
        closure_variables      = function_body.getClosureVariables(),
        defaults_identifier    = defaults_identifier,
        kw_defaults_identifier = kw_defaults_identifier,
        annotations_identifier = annotations_identifier,
        source_ref             = function_body.getSourceReference(),
        function_doc           = function_body.getDoc(),
        is_generator           = function_body.isGenerator()
    )

    context.addHelperCode( function_identifier, maker_code )

    function_decl = Generator.getFunctionMakerDecl(
        function_identifier    = function_body.getCodeName(),
        defaults_identifier    = defaults_identifier,
        kw_defaults_identifier = kw_defaults_identifier,
        annotations_identifier = annotations_identifier,
        closure_variables      = function_body.getClosureVariables()
    )

    if function_body.getClosureVariables() and not function_body.isGenerator():
        function_decl += "\n"

        function_decl += Generator.getFunctionContextDefinitionCode(
            context              = context,
            function_identifier  = function_body.getCodeName(),
            closure_variables    = function_body.getClosureVariables(),
        )

    context.addDeclaration(function_identifier, function_decl)

    return Generator.getFunctionCreationCode(
        function_identifier = function_body.getCodeName(),
        order_relevance     = order_relevance,
        default_args        = default_args,
        closure_variables   = function_body.getClosureVariables(),
        context             = context
    )


def generateFunctionBodyCode(function_body, context):
    function_identifier = function_body.getCodeName()

    if function_identifier in _generated_functions:
        return _generated_functions[ function_identifier ]

    if function_body.needsCreation():
        function_context = Contexts.PythonFunctionCreatedContext(
            parent   = context,
            function = function_body
        )
    else:
        function_context = Contexts.PythonFunctionDirectContext(
            parent   = context,
            function = function_body
        )

    # TODO: Generate both codes, and base direct/etc. decisions on context.
    function_codes = generateStatementSequenceCode(
        statement_sequence = function_body.getBody(),
        allow_none         = True,
        context            = function_context
    )

    function_codes = function_codes or []

    parameters = function_body.getParameters()

    if function_body.isGenerator():
        function_code = Generator.getGeneratorFunctionCode(
            context                = function_context,
            function_name          = function_body.getFunctionName(),
            function_identifier    = function_identifier,
            parameters             = parameters,
            closure_variables      = function_body.getClosureVariables(),
            user_variables         = function_body.getUserLocalVariables(),
            temp_variables         = function_body.getTempVariables(),
            source_ref             = function_body.getSourceReference(),
            function_codes         = function_codes,
            function_doc           = function_body.getDoc()
        )
    else:
        function_code = Generator.getFunctionCode(
            context                = function_context,
            function_name          = function_body.getFunctionName(),
            function_identifier    = function_identifier,
            parameters             = parameters,
            closure_variables      = function_body.getClosureVariables(),
            user_variables         = function_body.getUserLocalVariables(),
            temp_variables         = function_body.getTempVariables(),
            function_codes         = function_codes,
            function_doc           = function_body.getDoc(),
            file_scope             = Generator.getExportScopeCode(
                cross_module = function_body.isCrossModuleUsed()
            )
        )



    return function_code

def generateAttributeLookupCode(source, attribute_name, context):
    if attribute_name == "__dict__":
        return Generator.getAttributeLookupDictSlotCode( source )
    elif attribute_name == "__class__":
        return Generator.getAttributeLookupClassSlotCode( source )
    else:
        return Generator.getAttributeLookupCode(
            attribute = Generator.getConstantHandle(
                context  = context,
                constant = attribute_name
            ),
            source    = source
        )

def generateOperationCode(operator, operands, context):
    return Generator.getOperationCode(
        order_relevance = getOrderRelevance( operands ),
        operator        = operator,
        identifiers     = generateExpressionsCode(
            expressions  = operands,
            context      = context
        ),
        context         = context
    )

def generateComparisonExpressionCode(comparison_expression, context):
    left = generateExpressionCode(
        expression = comparison_expression.getLeft(),
        context    = context
    )
    right = generateExpressionCode(
        expression = comparison_expression.getRight(),
        context    = context
    )

    return Generator.getComparisonExpressionCode(
        comparator      = comparison_expression.getComparator(),
        order_relevance = getOrderRelevance(
            comparison_expression.getVisitableNodes()
        ),
        left            = left,
        right           = right,
        context         = context
    )

def generateDictionaryCreationCode(pairs, context):
    args = []

    # Strange as it is, CPython evalutes the key/value pairs strictly in order,
    # but for each pair, the value first.
    for pair in pairs:
        args.append(pair.getValue())
        args.append(pair.getKey())

    if _areConstants(args):
        constant = {}

        for pair in pairs:
            key = pair.getKey()
            value = pair.getValue()

            constant[key.getConstant()] = value.getConstant()

        return Generator.getConstantHandle(
            context  = context,
            constant = constant
        )
    else:
        args_identifiers = generateExpressionsCode(
            expressions = args,
            context     = context
        )

        return Generator.getDictionaryCreationCode(
            context          = context,
            order_relevance  = getOrderRelevance(args),
            args_identifiers = args_identifiers
        )

def generateSetCreationCode(elements, context):
    element_identifiers = generateExpressionsCode(
        expressions = elements,
        context     = context
    )

    return Generator.getSetCreationCode(
        order_relevance     = getOrderRelevance( elements ),
        element_identifiers = element_identifiers,
        context             = context
    )

def _areConstants(expressions):
    for expression in expressions:
        if not expression.isExpressionConstantRef():
            return False

        if expression.isMutable():
            return False
    else:
        return True

def generateSliceRangeIdentifier(lower, upper, context):
    def isSmallNumberConstant(node):
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

def generateSliceAccessIdentifiers(sliced, lower, upper, context):
    lower, upper = generateSliceRangeIdentifier( lower, upper, context )

    sliced = generateExpressionCode(
        expression = sliced,
        context    = context
    )

    return sliced, lower, upper

_slicing_available = Utils.python_version < 300

def decideSlicing(lower, upper):
    return _slicing_available and                       \
           ( lower is None or lower.isIndexable() ) and \
           ( upper is None or upper.isIndexable() )

def generateSubscriptLookupCode(expression, context):
    return Generator.getSubscriptLookupCode(
        order_relevance = getOrderRelevance(
            ( expression.getLookupSource(), expression.getSubscript() )
        ),
        subscript       = generateExpressionCode(
            expression = expression.getSubscript(),
            context    = context
        ),
        source          = generateExpressionCode(
            expression = expression.getLookupSource(),
            context    = context
        ),
        context         = context
    )

def generateSliceLookupCode(expression, context):
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
                order_relevance = getOrderRelevance(
                    (
                        expression.getLookupSource(),
                        expression.getLower(),
                        expression.getUpper()
                    ),
                    allow_none  = True,
                ),
                source          = generateExpressionCode(
                    expression = expression.getLookupSource(),
                    context    = context
                ),
                lower           = generateExpressionCode(
                    expression = lower,
                    allow_none = True,
                    context    = context
                ),
                upper           = generateExpressionCode(
                    expression = upper,
                    allow_none = True,
                    context    = context
                ),
                context         = context
            )
        else:
            order_relevance = getOrderRelevance(
                ( expression.getLookupSource(), lower, upper, None ),
                allow_none = True
            )

            return Generator.getSubscriptLookupCode(
                order_relevance = (
                    order_relevance[0],
                    Generator.pickFirst( order_relevance[1:] )
                ),
                source          = generateExpressionCode(
                    expression = expression.getLookupSource(),
                    context    = context
                ),
                subscript       = Generator.getSliceObjectCode(
                    order_relevance = order_relevance[1:],
                    lower           = generateExpressionCode(
                        expression = lower,
                        allow_none = True,
                        context    = context
                    ),
                    upper           = generateExpressionCode(
                        expression = upper,
                        allow_none = True,
                        context    = context
                    ),
                    step            = None,
                    context         = context
                ),
                context         = context
            )

def generateCallCode(call_node, context):
    called_identifier = generateExpressionCode(
        expression = call_node.getCalled(),
        context    = context
    )

    argument_dictionary  = generateExpressionCode(
        expression = call_node.getCallKw(),
        context    = context
    )

    # Avoid non-empty arguments for positional or keywords, where they are in
    # fact empty.
    if argument_dictionary is not None and \
       argument_dictionary.isConstantIdentifier() and \
       argument_dictionary.getConstant() == {}:
        argument_dictionary = None

    call_args = call_node.getCallArgs()

    if argument_dictionary is None:
        if call_args.isExpressionConstantRef() and \
           call_args.getConstant() == ():
            return Generator.getCallCodeNoArgs(
                called_identifier = called_identifier
            )
        elif call_args.isExpressionMakeTuple():
            return Generator.getCallCodePosArgsQuick(
               order_relevance   = getOrderRelevance(
                   ( call_node.getCalled(), ) + call_args.getElements(),
                ),
                called_identifier = called_identifier,
                arguments         = generateExpressionsCode(
                    expressions = call_args.getElements(),
                    context     = context
                ),
                context           = context
            )
        elif call_args.isExpressionConstantRef():
            return Generator.getCallCodePosArgsQuick(
                order_relevance   =
                   ( call_node.isOrderRelevant(), ) + \
                   ( None, ) * len( call_args.getConstant() ),
                called_identifier = called_identifier,
                arguments         = [
                    Generator.getConstantAccess(
                        constant = element,
                        context  = context
                    )
                    for element in
                    call_args.getConstant()
                ],
                context           = context
            )
        else:
            return Generator.getCallCodePosArgs(
                order_relevance   = getOrderRelevance(
                    ( call_node.getCalled(), call_node.getCallArgs() ),
                ),
                called_identifier = called_identifier,
                argument_tuple    = generateExpressionCode(
                    expression = call_args,
                    context    = context
                ),
                context           = context
            )
    else:
        argument_tuple = generateExpressionCode(
            expression = call_args,
            context    = context
        )

        if argument_tuple is None:
            return Generator.getCallCodeKeywordArgs(
                order_relevance     = getOrderRelevance(
                    ( call_node.getCalled(), call_node.getCallKw() ),
                ),
                called_identifier   = called_identifier,
                argument_dictionary = argument_dictionary,
                context             = context
            )
        else:
            return Generator.getCallCodePosKeywordArgs(
                order_relevance     = getOrderRelevance(
                    ( call_node.getCalled(), call_node.getCallArgs(),
                      call_node.getCallKw() ),
                ),
                called_identifier   = called_identifier,
                argument_dictionary = argument_dictionary,
                argument_tuple      = argument_tuple,
                context             = context
            )


def _decideLocalsMode(provider):
    # TODO: This information should be in the node instead, and not decided
    # during code generation, as optimization needs to know it. It should also
    # be sticky and safe against inline this way.
    if Utils.python_version >= 300:
        mode = "updated"
    elif provider.isExpressionFunctionBody() and ( provider.isEarlyClosure() or provider.isUnoptimized() ):
        mode = "updated"
    else:
        mode = "copy"

    return mode

def generateBuiltinLocalsCode(locals_node, context):
    provider = locals_node.getParentVariableProvider()

    return Generator.getLoadLocalsCode(
        context  = context,
        provider = provider,
        mode     = _decideLocalsMode( provider )
    )

def generateBuiltinDir0Code(dir_node, context):
    provider = dir_node.getParentVariableProvider()

    return Generator.getLoadDirCode(
        context  = context,
        provider = provider
    )

def generateBuiltinDir1Code(dir_node, context):
    return Generator.getBuiltinDir1Code(
        identifier = generateExpressionCode(
            expression = dir_node.getValue(),
            context    = context
        )
    )

def generateExpressionsCode(expressions, context, allow_none = False):
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

def getOrderRelevance(expressions, allow_none = False):
    result = []

    for expression in expressions:
        if expression is None and allow_none:
            result.append(None)
        elif expression.isOrderRelevant():
            result.append(expression.getSourceReference())
        else:
            result.append(None)


    return result

def _generateExpressionCode(expression, context, allow_none):
    # This is a dispatching function with a branch per expression node type, and
    # therefore many statements even if every branch is small
    # pylint: disable=R0912,R0915

    if expression is None and allow_none:
        return None

    # Make sure we don't generate code twice for any node, this uncovers bugs
    # where nodes are shared in the tree, which is not allowed.
    assert not hasattr(expression, "code_generated"), expression
    expression.code_generated = True

    def makeExpressionCode(expression, allow_none = False):
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
            Tracing.printError("Illegal variable reference, not resolved.")

            expression.dump()
            assert False, (
                expression.getSourceReference(),
                expression.getVariableName()
            )

        identifier = Generator.getVariableHandle(
            variable = expression.getVariable(),
            context  = context
        )
    elif expression.isExpressionTempVariableRef():
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
        assert expression.getPairs()

        identifier = generateDictionaryCreationCode(
            pairs   = expression.getPairs(),
            context = context
        )
    elif expression.isExpressionCall():
        identifier = generateCallCode(
            call_node = expression,
            context   = context
        )
    elif expression.isExpressionFunctionCall():
        identifier = generateFunctionCallCode(
            call_node = expression,
            context   = context
        )
    elif expression.isExpressionAttributeLookup():
        identifier = generateAttributeLookupCode(
            source         = makeExpressionCode( expression.getLookupSource() ),
            attribute_name = expression.getAttributeName(),
            context        = context
        )
    elif expression.isExpressionSpecialAttributeLookup():
        identifier = Generator.getSpecialAttributeLookupCode(
            attribute = Generator.getConstantHandle(
                context  = context,
                constant = expression.getAttributeName()
            ),
            source    = makeExpressionCode( expression.getLookupSource() ),
        )
    elif expression.isExpressionBuiltinHasattr():
        identifier = Generator.getAttributeCheckCode(
            order_relevance = getOrderRelevance(
                expression.getVisitableNodes()
            ),
            attribute       = makeExpressionCode(
                expression.getAttribute()
            ),
            source          = makeExpressionCode(
                expression.getLookupSource()
            ),
            context         = context
        )
    elif expression.isExpressionBuiltinGetattr():
        identifier = Generator.getAttributeGetCode(
            order_relevance = getOrderRelevance(
                (
                    expression.getLookupSource(),
                    expression.getAttribute(),
                    expression.getDefault(),
                ),
                allow_none = True
            ),
            source          = makeExpressionCode(
                expression.getLookupSource()
            ),
            attribute       = makeExpressionCode(
                expression.getAttribute()
            ),
            default         = makeExpressionCode(
                expression.getDefault(),
                allow_none = True
            ),
            context         = context
        )
    elif expression.isExpressionBuiltinSetattr():
        identifier = Generator.getAttributeSetCode(
            order_relevance = getOrderRelevance(
                expression.getVisitableNodes()
            ),
            source          = makeExpressionCode(
                expression.getLookupSource()
            ),
            attribute       = makeExpressionCode(
                expression.getAttribute()
            ),
            value           = makeExpressionCode(
                expression.getValue()
            ),
            context         = context
        )
    elif expression.isExpressionImportName():
        identifier = Generator.getImportNameCode(
            import_name = Generator.getConstantHandle(
                context  = context,
                constant = expression.getImportName()
            ),
            module      = makeExpressionCode(
                expression.getModule()
            )
        )
    elif expression.isExpressionSubscriptLookup():
        identifier = generateSubscriptLookupCode(
            expression = expression,
            context    = context
        )
    elif expression.isExpressionSliceLookup():
        identifier = generateSliceLookupCode(
            expression = expression,
            context    = context
        )
    elif expression.isExpressionSliceObject():
        identifier = Generator.getSliceObjectCode(
            order_relevance = getOrderRelevance(
                (
                    expression.getLower(),
                    expression.getUpper(),
                    expression.getStep()
                ),
                allow_none = True
            ),
            lower           = makeExpressionCode(
                expression = expression.getLower(),
                allow_none = True
            ),
            upper           = makeExpressionCode(
                expression = expression.getUpper(),
                allow_none = True
            ),
            step            = makeExpressionCode(
                expression = expression.getStep(),
                allow_none = True
            ),
            context         = context
        )
    elif expression.isExpressionConditional():
        identifier = Generator.getConditionalExpressionCode(
            condition_code = generateConditionCode(
                condition = expression.getCondition(),
                context   = context
            ),
            identifier_yes = makeExpressionCode(
                expression.getExpressionYes()
            ),
            identifier_no  = makeExpressionCode( expression.getExpressionNo() )
        )
    elif expression.isExpressionBuiltinRange1():
        identifier = Generator.getBuiltinRange1Code(
            value = makeExpressionCode( expression.getLow() )
        )
    elif expression.isExpressionBuiltinRange2():
        identifier = Generator.getBuiltinRange2Code(
            order_relevance = getOrderRelevance(
                expression.getVisitableNodes()
            ),
            low             = makeExpressionCode( expression.getLow() ),
            high            = makeExpressionCode( expression.getHigh() ),
            context         = context
        )
    elif expression.isExpressionBuiltinRange3():
        identifier = Generator.getBuiltinRange3Code(
            order_relevance = getOrderRelevance(
                expression.getVisitableNodes()
            ),
            low             = makeExpressionCode( expression.getLow() ),
            high            = makeExpressionCode( expression.getHigh() ),
            step            = makeExpressionCode( expression.getStep() ),
            context         = context
        )
    elif expression.isExpressionBuiltinXrange():
        identifier = Generator.getBuiltinXrangeCode(
            order_relevance = getOrderRelevance(
                (
                    expression.getLow(),
                    expression.getHigh(),
                    expression.getStep()
                ),
                allow_none = True
            ),
            low             = makeExpressionCode(
                expression.getLow(),
                allow_none = False
            ),
            high            = makeExpressionCode(
                expression.getHigh(),
                allow_none = True
            ),
            step            = makeExpressionCode(
                expression.getStep(),
                allow_none = True
            ),
            context         = context
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
            order_relevance = getOrderRelevance(
                (
                    expression.getFilename(),
                    expression.getMode(),
                    expression.getBuffering()
                ),
                allow_none = True
            ),
            filename        = makeExpressionCode(
                expression = expression.getFilename(),
                allow_none = True
            ),
            mode            = makeExpressionCode(
                expression = expression.getMode(),
                allow_none = True
            ),
            buffering       = makeExpressionCode(
                expression = expression.getBuffering(),
                allow_none = True
            ),
            context         = context
        )
    elif expression.isExpressionFunctionCreation():
        identifier = generateFunctionCreationCode(
            function_body  = expression.getFunctionRef().getFunctionBody(),
            defaults       = expression.getDefaults(),
            kw_defaults    = expression.getKwDefaults(),
            annotations    = expression.getAnnotations(),
            context        = context
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
            in_handler = expression.isExceptionPreserving()
        )
    elif expression.isExpressionYieldFrom():
        identifier = Generator.getYieldFromCode(
            identifier = makeExpressionCode(
                expression = expression.getExpression()
            ),
            in_handler = expression.isExceptionPreserving()
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
            order_relevance     = getOrderRelevance(
                expression.getVisitableNodes()
            ),
            callable_identifier = makeExpressionCode(
                expression.getCallable()
            ),
            sentinel_identifier = makeExpressionCode(
                expression.getSentinel()
            ),
            context             = context
        )
    elif expression.isExpressionBuiltinNext1():
        identifier = Generator.getBuiltinNext1Code(
            value = makeExpressionCode(
                expression.getValue()
            )
        )
    elif expression.isExpressionSpecialUnpack():
        identifier = Generator.getUnpackNextCode(
            iterator_identifier = makeExpressionCode( expression.getValue() ),
            count               = expression.getCount()
        )
    elif expression.isExpressionBuiltinNext2():
        identifier = Generator.getBuiltinNext2Code(
            order_relevance     = getOrderRelevance(
                expression.getVisitableNodes()
            ),
            iterator_identifier = makeExpressionCode(
                expression.getIterator()
            ),
            default_identifier  = makeExpressionCode(
                expression.getDefault()
            ),
            context             = context
        )
    elif expression.isExpressionBuiltinType1():
        identifier = Generator.getBuiltinType1Code(
            value = makeExpressionCode( expression.getValue() )
        )
    elif expression.isExpressionBuiltinType3():
        identifier = Generator.getBuiltinType3Code(
            order_relevance  = getOrderRelevance(
                expression.getVisitableNodes()
            ),
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
        # assert not expression.hasOnlyConstantArguments()

        identifier = Generator.getBuiltinDictCode(
            seq_identifier  = makeExpressionCode(
                expression = expression.getPositionalArgument(),
                allow_none = True
            ),
            dict_identifier = generateDictionaryCreationCode(
                pairs    = expression.getNamedArgumentPairs(),
                context  = context
            )
        )
    elif expression.isExpressionBuiltinSet():
        identifier = Generator.getBuiltinSetCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif Utils.python_version < 300 and expression.isExpressionBuiltinStr():
        identifier = Generator.getBuiltinStrCode(
            identifier = makeExpressionCode( expression.getValue() )
        )
    elif Utils.python_version < 300 and expression.isExpressionBuiltinUnicode() or \
         Utils.python_version >= 300 and expression.isExpressionBuiltinStr():
        encoding = expression.getEncoding()
        errors = expression.getErrors()

        if encoding is None and errors is None:
            identifier = Generator.getBuiltinUnicode1Code(
                identifier = makeExpressionCode(
                    expression = expression.getValue()
                )
            )
        else:
            identifier = Generator.getBuiltinUnicode3Code(
                order_relevance = getOrderRelevance(
                    (
                        expression.getValue(),
                        encoding,
                        errors
                    ),
                    allow_none = True
                ),
                identifier      = makeExpressionCode(
                    expression = expression.getValue()
                ),
                encoding        = makeExpressionCode(
                    expression = encoding,
                    allow_none = True
                ),
                errors          = makeExpressionCode(
                    expression = errors,
                    allow_none = True
                ),
                context         = context
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
        # Missed optimization opportunity, please report.
        if Options.isDebug():
            parent = expression.parent
            assert parent.isExpressionSideEffects() or \
                   parent.isExpressionConditional(), \
                   ( expression, expression.parent )

        identifier = Generator.getRaiseExceptionExpressionCode(
            exception_type  = makeExpressionCode(
                expression = expression.getExceptionType()
            ),
            exception_value = makeExpressionCode(
                expression = expression.getExceptionValue(),
                allow_none = True
            ),
            context         = context
        )
    elif expression.isExpressionBuiltinMakeException():
        identifier = Generator.getMakeBuiltinExceptionCode(
            exception_type  = expression.getExceptionName(),
            exception_args  = generateExpressionsCode(
                expressions  = expression.getArgs(),
                context      = context
            ),
            order_relevance = getOrderRelevance( expression.getArgs() ),
            context         = context
        )
    elif expression.isExpressionBuiltinOriginalRef():
        assert not expression.isExpressionBuiltinRef()

        identifier = Generator.getBuiltinOriginalRefCode(
            builtin_name = expression.getBuiltinName(),
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
        identifier = Generator.getAssignmentTempKeeperCode(
            variable          = expression.getVariable(),
            source_identifier = makeExpressionCode(
                expression.getAssignSource()
            ),
            context           = context
        )
    elif expression.isExpressionBuiltinInt():
        value = expression.getValue()
        base = expression.getBase()

        assert value is not None or base is not None

        if base is None:
            identifier = Generator.getBuiltinInt1Code(
                identifier = makeExpressionCode(
                    value,
                    allow_none = True
                ),
                context    = context
            )
        else:
            identifier = Generator.getBuiltinInt2Code(
                order_relevance = getOrderRelevance(
                    ( value, base ),
                    allow_none = True
                ),
                identifier      = makeExpressionCode(
                    value,
                    allow_none = True
                ),
                base            = makeExpressionCode(
                    expression.getBase(),
                ),
                context         = context
            )
    elif Utils.python_version < 300 and expression.isExpressionBuiltinLong():
        value = expression.getValue()
        base = expression.getBase()

        assert value is not None or base is not None

        if base is None:
            identifier = Generator.getBuiltinLong1Code(
                identifier = makeExpressionCode(
                    value,
                    allow_none = True
                ),
                context    = context
            )
        else:
            identifier = Generator.getBuiltinLong2Code(
                order_relevance = getOrderRelevance(
                    ( value, base ),
                    allow_none = True
                ),
                identifier      = makeExpressionCode(
                    value,
                    allow_none = True
                ),
                base            = makeExpressionCode(
                    expression.getBase(),
                ),
                context         = context
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
    # TODO: These operations need order enforcement, once they are added by
    # optimization and not be re-formulations only.
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
    elif expression.isExpressionDictOperationGet():
        identifier = Generator.getDictOperationGetCode(
            dict_identifier    = makeExpressionCode( expression.getDict() ),
            key_identifier     = makeExpressionCode( expression.getKey() ),
        )
    elif expression.isExpressionTempKeeperRef():
        identifier = Generator.getTempKeeperHandle(
            variable = expression.getVariable(),
            context  = context
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
        identifier = Generator.getBuiltinSuperCode(
            order_relevance   = getOrderRelevance(
                ( expression.getType(), expression.getObject() ),
                allow_none = True
            ),
            type_identifier   = makeExpressionCode(
                expression.getType(),
                allow_none = True
            ),
            object_identifier = makeExpressionCode(
                expression.getObject(),
                allow_none = True
            ),
            context           = context
        )
    elif expression.isExpressionBuiltinIsinstance():
        identifier = Generator.getBuiltinIsinstanceCode(
            order_relevance = getOrderRelevance(
                expression.getVisitableNodes()
            ),
            inst_identifier = makeExpressionCode( expression.getInstance() ),
            cls_identifier  = makeExpressionCode( expression.getCls() ),
            context         = context
        )
    elif expression.isExpressionSelectMetaclass():
        identifier = Generator.getSelectMetaclassCode(
            metaclass_identifier = makeExpressionCode(
                expression.getMetaclass(),
                allow_none = True
            ),
            bases_identifier     = makeExpressionCode( expression.getBases() ),
            context              = context
        )
    elif Utils.python_version < 300 and \
         expression.isExpressionBuiltinExecfile():
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

def generateExpressionCode(expression, context, allow_none = False):
    try:
        return _generateExpressionCode(
            expression = expression,
            context    = context,
            allow_none = allow_none
        )
    except:
        Tracing.printError(
            "Problem with %r at %s" % (
                expression,
                expression.getSourceReference()
            )
        )
        raise

def generateAssignmentVariableCode(variable_ref, value, context):
    return Generator.getVariableAssignmentCode(
        variable   = variable_ref.getVariable(),
        identifier = value,
        context    = context
    )

def generateAssignmentAttributeCode( lookup_source, attribute_name, value,
                                     context ):
    target          = generateExpressionCode(
        expression = lookup_source,
        context    = context
    )
    identifer = generateExpressionCode(
        expression = value,
        context    = context
    )

    order_relevance = getOrderRelevance( ( value, lookup_source ) )

    if attribute_name == "__dict__":
        return Generator.getAttributeAssignmentDictSlotCode(
            order_relevance = order_relevance,
            target          = target,
            identifier      = identifer
        )
    elif attribute_name == "__class__":
        return Generator.getAttributeAssignmentClassSlotCode(
            order_relevance = order_relevance,
            target          = target,
            identifier      = identifer
        )
    else:
        order_relevance.append( None )

        return Generator.getAttributeAssignmentCode(
            order_relevance = order_relevance,
            target          = target,
            attribute       = Generator.getConstantHandle(
                context  = context,
                constant = attribute_name
            ),
            identifier      = identifer
        )

def generateAssignmentSliceCode(lookup_source, lower, upper, value, context):
    value_identifier = generateExpressionCode(
        expression = value,
        context    = context
    )

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
            identifier = value_identifier
        )
    else:
        if _slicing_available:
            return Generator.getSliceAssignmentCode(
                order_relevance = getOrderRelevance(
                    ( value, lookup_source, lower, upper ),
                    allow_none = True
                ),
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
                identifier = value_identifier
            )
        else:
            order_relevance = getOrderRelevance(
                ( value, lookup_source, lower, upper, None ),
                allow_none = True
            )

            return Generator.getSubscriptAssignmentCode(
                order_relevance = (
                    order_relevance[0],
                    order_relevance[1],
                    Generator.pickFirst( order_relevance[2:] )
                ),
                subscribed = generateExpressionCode(
                    expression = lookup_source,
                    context    = context
                ),
                subscript  = Generator.getSliceObjectCode(
                    order_relevance = order_relevance[2:],
                    lower  = generateExpressionCode(
                        expression = lower,
                        allow_none = True,
                        context    = context
                    ),
                    upper           = generateExpressionCode(
                        expression = upper,
                        allow_none = True,
                        context    = context
                    ),
                    step            = None,
                    context         = context
                ),
                identifier = value_identifier
            )


def generateDelVariableCode(variable_ref, tolerant, context):
    return Generator.getVariableDelCode(
        variable = variable_ref.getVariable(),
        tolerant = tolerant,
        context  = context
    )

def generateDelSubscriptCode(subscribed, subscript, context):
    return Generator.getSubscriptDelCode(
        order_relevance = getOrderRelevance(
            ( subscribed, subscript )
        ),
        subscribed      = generateExpressionCode(
            expression = subscribed,
            context    = context
        ),
        subscript       = generateExpressionCode(
            expression = subscript,
            context    = context
        )
    )

def generateDelSliceCode(lookup_source, lower, upper, context):
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
        order_relevance = getOrderRelevance(
            ( lookup_source, lower, upper, None ),
            allow_none = True
        )

        return Generator.getSubscriptDelCode(
            order_relevance = (
                order_relevance[0],
                Generator.pickFirst( order_relevance[1:] )
            ),
            subscribed      = generateExpressionCode(
                expression = lookup_source,
                context    = context
            ),
            subscript       = Generator.getSliceObjectCode(
                order_relevance = order_relevance[1:],
                lower           = generateExpressionCode(
                    expression = lower,
                    allow_none = True,
                    context    = context
                ),
                upper           = generateExpressionCode(
                    expression = upper,
                    allow_none = True,
                    context    = context
                ),
                step            = None,
                context         = context
            )
        )

def generateDelAttributeCode(statement, context):
    return Generator.getAttributeDelCode(
        target    = generateExpressionCode(
            expression = statement.getLookupSource(),
            context    = context
        ),
        attribute = Generator.getConstantHandle(
            context  = context,
            constant = statement.getAttributeName()
        )
    )

def _generateEvalCode(node, context):
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

    order_relevance = getOrderRelevance(
        ( node.getSourceCode(), globals_value, locals_value ),
        allow_none = True
    )

    identifier = Generator.getEvalCode(
        order_relevance     = order_relevance,
        exec_code           = generateExpressionCode(
            expression = node.getSourceCode(),
            context    = context
        ),
        globals_identifier  = globals_identifier,
        locals_identifier   = locals_identifier,
        filename_identifier = Generator.getConstantHandle(
            constant = filename,
            context  = context
        ),
        mode_identifier    = Generator.getConstantHandle(
            constant = "eval" if node.isExpressionBuiltinEval() else "exec",
            context  = context
        ),
        future_flags       = Generator.getFutureFlagsCode(
            future_spec = node.getSourceReference().getFutureSpec()
        ),
        context            = context
    )

    return identifier

def generateEvalCode(eval_node, context):
    return _generateEvalCode(
        node    = eval_node,
        context = context
    )

def generateExecfileCode(execfile_node, context):
    return _generateEvalCode(
        node    = execfile_node,
        context = context
    )

def generateExecCode(exec_def, context):
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
        ),
        source_ref         = exec_def.getSourceReference()
    )

def generateTryFinallyCode(statement, context):
    try_count = context.allocateTryNumber()

    context.setTryFinallyCount( try_count )

    code_final             = generateStatementSequenceCode(
        statement_sequence = statement.getBlockFinal(),
        context            = context
    )

    context.removeFinallyCount()

    code_tried             = generateStatementSequenceCode(
        statement_sequence = statement.getBlockTry(),
        context            = context
    )

    needs_return_value_catch   = statement.needsExceptionReturnValueCatcher()
    needs_return_value_reraise = statement.needsExceptionReturnValueReraiser()

    return Generator.getTryFinallyCode(
        code_tried                 = code_tried,
        code_final                 = code_final,
        needs_break                = statement.needsExceptionBreak(),
        needs_continue             = statement.needsExceptionContinue(),
        needs_return_value_catch   = needs_return_value_catch,
        needs_return_value_reraise = needs_return_value_reraise,
        aborting                   = statement.isStatementAborting(),
        try_count                  = try_count,
        context                    = context
    )

def generateTryExceptCode(statement, context):
    tried_block = statement.getBlockTry()

    assert tried_block.mayRaiseException( BaseException )

    if statement.isStatementTryExceptOptimized():
        tried_statements = tried_block.getStatements()

        assert len( tried_statements ) == 1
        tried_statement = tried_statements[0]

        source = tried_statement.getAssignSource()

        assert source.isExpressionBuiltinNext1()
        assert not source.getValue().mayRaiseException( BaseException )

        handlers = statement.getExceptionHandlers()
        assert len( handlers ) == 1

        temp_identifier = Generator.getTryNextExceptStopIterationIdentifier(
            context = context
        )

        source_identifier = generateExpressionCode(
            expression = source.getValue(),
            context    = context
        )

        assign_code = generateAssignmentVariableCode(
            variable_ref = tried_statement.getTargetVariableRef(),
            value        = temp_identifier,
            context      = context
        )

        handler_code      = generateStatementSequenceCode(
            statement_sequence = handlers[0].getExceptionBranch(),
            allow_none         = True,
            context            = context
        )

        return Generator.getTryNextExceptStopIterationCode(
            temp_identifier   = temp_identifier,
            assign_code       = assign_code,
            handler_code      = handler_code,
            source_identifier = source_identifier
        )

    handler_codes = []

    code_tried = generateStatementSequenceCode(
        statement_sequence = tried_block,
        context            = context,
    )


    for count, handler in enumerate( statement.getExceptionHandlers() ):
        Generator.pushLineNumberBranch()

        exception_identifiers = generateExpressionsCode(
            expressions = handler.getExceptionTypes(),
            allow_none  = True,
            context     = context
        )

        exception_branch = handler.getExceptionBranch()

        handler_code = generateStatementSequenceCode(
            statement_sequence = exception_branch,
            allow_none         = True,
            context            = context
        )

        handler_codes += Generator.getTryExceptHandlerCode(
            exception_identifiers = exception_identifiers,
            handler_code          = handler_code,
            first_handler         = count == 0,
            # TODO: Check if the code may access traceback or not, we can create
            # more efficient code if not, which ought to be the common case.
            needs_frame_detach    = exception_branch is not None
        )

        Generator.popLineNumberBranch()

    Generator.mergeLineNumberBranches()

    return Generator.getTryExceptCode(
        context       = context,
        code_tried    = code_tried,
        handler_codes = handler_codes
    )

def generateRaiseCode(statement, context):
    exception_type  = statement.getExceptionType()
    exception_value = statement.getExceptionValue()
    exception_tb    = statement.getExceptionTrace()
    exception_cause = statement.getExceptionCause()

    # Exception cause is only possible with simple raise form.
    if exception_cause is not None:
        assert exception_type is not None
        assert exception_value is None
        assert exception_tb is None

        return Generator.getRaiseExceptionWithCauseCode(
            order_relevance = getOrderRelevance(
                ( statement.getExceptionType(), statement.getExceptionCause() )
            ),
            exception_type  = generateExpressionCode(
                expression  = statement.getExceptionType(),
                context     = context
            ),
            exception_cause = generateExpressionCode(
                expression  = statement.getExceptionCause(),
                context     = context
            ),
            context         = context
        )
    elif exception_type is None:
        assert exception_cause is None

        return Generator.getReRaiseExceptionCode(
            local = statement.isReraiseExceptionLocal(),
            final = context.getTryFinallyCount()
                       if statement.isReraiseExceptionFinally()
                    else None,
        )
    elif exception_value is None and exception_tb is None:
        return Generator.getRaiseExceptionWithTypeCode(
            order_relevance = getOrderRelevance(
                ( exception_type, ),
            ),
            exception_type  = generateExpressionCode(
                expression  = exception_type,
                context     = context
            ),
            context        = context
        )
    elif exception_tb is None:
        return Generator.getRaiseExceptionWithValueCode(
            order_relevance = getOrderRelevance(
                ( exception_type, exception_value ),
            ),
            exception_type  = generateExpressionCode(
                expression = exception_type,
                context    = context
            ),
            exception_value = generateExpressionCode(
                expression = exception_value,
                context    = context
            ),
            implicit        = statement.isImplicit(),
            context         = context
        )
    else:
        return Generator.getRaiseExceptionWithTracebackCode(
            order_relevance = getOrderRelevance(
                ( exception_type, exception_value, exception_tb ),
            ),
            exception_type  = generateExpressionCode(
                expression = exception_type,
                context    = context
            ),
            exception_value = generateExpressionCode(
                expression = exception_value,
                context    = context
            ),
            exception_tb    = generateExpressionCode(
                expression = exception_tb,
                context    = context
            )
        )

def generateImportModuleCode(expression, context):
    provider = expression.getParentVariableProvider()

    globals_dict = Generator.getLoadGlobalsCode(
        context = context
    )

    if provider.isPythonModule():
        locals_dict = globals_dict
    else:
        locals_dict  = generateBuiltinLocalsCode(
            locals_node = expression,
            context     = context
        )

    order_relevance = [ None ] * 5

    return Generator.getBuiltinImportCode(
        order_relevance    = order_relevance,
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
        ),
        context            = context
    )

def generateBuiltinImportCode(expression, context):
    globals_dict = generateExpressionCode(
        expression = expression.getGlobals(),
        allow_none = True,
        context    = context
    )

    locals_dict = generateExpressionCode(
        expression = expression.getLocals(),
        allow_none = True,
        context    = context
    )

    order_relevance = getOrderRelevance(
        (
            expression.getImportName(),
            expression.getGlobals(),
            expression.getLocals(),
            expression.getFromList(),
            expression.getLevel()
        ),
        allow_none = True
    )

    if globals_dict is None:
        globals_dict = Generator.getLoadGlobalsCode(
            context = context
        )

    if locals_dict is None:
        provider = expression.getParentVariableProvider()

        if provider.isPythonModule():
            locals_dict = globals_dict
        else:
            locals_dict  = generateBuiltinLocalsCode(
                locals_node = expression,
                context     = context
            )

    return Generator.getBuiltinImportCode(
        order_relevance   = order_relevance,
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
        ),
        context           = context
    )


def generateImportStarCode(statement, context):
    return Generator.getImportFromStarCode(
        module_identifier = generateImportModuleCode(
            expression = statement.getModule(),
            context    = context
        ),
        context     = context
    )

def generatePrintCode(statement, target_file, context):
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

def generateBranchCode(statement, context):
    condition_code = generateConditionCode(
        condition = statement.getCondition(),
        context   = context
    )

    Generator.pushLineNumberBranch()
    yes_codes      = generateStatementSequenceCode(
        statement_sequence = statement.getBranchYes(),
        allow_none         = True,
        context            = context
    )
    Generator.popLineNumberBranch()

    Generator.pushLineNumberBranch()
    no_codes       = generateStatementSequenceCode(
        statement_sequence = statement.getBranchNo(),
        allow_none         = True,
        context            = context
    )
    Generator.popLineNumberBranch()
    Generator.mergeLineNumberBranches()

    # Do not allow this, optimization must have avoided it.
    assert yes_codes is not None, statement

    return Generator.getBranchCode(
        condition_code = condition_code,
        yes_codes      = yes_codes,
        no_codes       = no_codes
    )

def generateLoopCode(statement, context):
    # The loop is re-entrant, therefore force setting the line number at start
    # again, even if the same as before.
    Generator.resetLineNumber()

    loop_body_codes = generateStatementSequenceCode(
        statement_sequence = statement.getLoopBody(),
        allow_none         = True,
        context            = context
    )

    return Generator.getLoopCode(
        loop_body_codes          = loop_body_codes,
        needs_break_exception    = statement.needsExceptionBreak(),
        needs_continue_exception = statement.needsExceptionContinue()
    )

def generateReturnCode(statement, context):
    return Generator.getReturnCode(
        identifier    = generateExpressionCode(
            expression = statement.getExpression(),
            context    = context
        ),
        via_exception = statement.isExceptionDriven(),
        context       = context
    )

def generateGeneratorReturnCode(statement, context):
    return Generator.getReturnCode(
        identifier    = generateExpressionCode(
            expression = statement.getExpression(),
            context    = context
        ),
        # TODO: Use the knowledge about actual need and return immediately if
        # possible.
        via_exception = True,
        context       = context
    )

def generateStatementCode(statement, context):
    try:
        statement_context = Contexts.PythonStatementContext( context )
        result = _generateStatementCode( statement, statement_context )
        local_inits = statement_context.getTempKeeperDecl()

        if local_inits:
            result = Generator.getBlockCode(
                local_inits + result.split( "\n" )
            )

        return result
    except:
        Tracing.printError(
            "Problem with %r at %s" % (
                statement,
                statement.getSourceReference()
            )
        )
        raise

def _generateStatementCode(statement, context):
    # This is a dispatching function with a branch per statement node type.
    # pylint: disable=R0912,R0915

    if not statement.isStatement():
        statement.dump()
        assert False

    def makeExpressionCode(expression, allow_none = False):
        if allow_none and expression is None:
            return None

        return generateExpressionCode(
            expression = expression,
            context    = context
        )

    if statement.isStatementAssignmentVariable():
        code = generateAssignmentVariableCode(
            variable_ref  = statement.getTargetVariableRef(),
            value         = makeExpressionCode( statement.getAssignSource() ),
            context       = context
        )
    elif statement.isStatementAssignmentAttribute():
        code = generateAssignmentAttributeCode(
            lookup_source  = statement.getLookupSource(),
            attribute_name = statement.getAttributeName(),
            value          = statement.getAssignSource(),
            context        = context
        )
    elif statement.isStatementAssignmentSubscript():
        code = Generator.getSubscriptAssignmentCode(
            order_relevance = getOrderRelevance(
                statement.getVisitableNodes()
            ),
            subscribed      = makeExpressionCode( statement.getSubscribed() ),
            subscript       = makeExpressionCode( statement.getSubscript() ),
            identifier      = makeExpressionCode( statement.getAssignSource() ),
        )
    elif statement.isStatementAssignmentSlice():
        code = generateAssignmentSliceCode(
            lookup_source  = statement.getLookupSource(),
            lower          = statement.getLower(),
            upper          = statement.getUpper(),
            value          = statement.getAssignSource(),
            context        = context
        )
    elif statement.isStatementDelVariable():
        code = generateDelVariableCode(
            variable_ref = statement.getTargetVariableRef(),
            tolerant     = statement.isTolerant(),
            context      = context
        )
    elif statement.isStatementDelSubscript():
        code = generateDelSubscriptCode(
            subscribed = statement.getSubscribed(),
            subscript  = statement.getSubscript(),
            context    = context
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
    elif statement.isStatementGeneratorReturn():
        code = generateGeneratorReturnCode(
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
            needs_exceptions = statement.isExceptionDriven()
        )
    elif statement.isStatementBreakLoop():
        code = Generator.getLoopBreakCode(
            needs_exceptions = statement.isExceptionDriven()
        )
    elif statement.isStatementImportStar():
        code = generateImportStarCode(
            statement = statement,
            context   = context
        )
    elif statement.isStatementTryFinally():
        code = generateTryFinallyCode(
            statement = statement,
            context   = context
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
    elif statement.isStatementSpecialUnpackCheck():
        code = Generator.getUnpackCheckCode(
            iterator_identifier = makeExpressionCode( statement.getIterator() ),
            count               = statement.getCount()
        )
    elif statement.isStatementDictOperationRemove():
        code = Generator.getDictOperationRemoveCode(
            dict_identifier = makeExpressionCode( statement.getDict() ),
            key_identifier  = makeExpressionCode( statement.getKey() )
        )
    elif statement.isStatementSetLocals():
        code = Generator.getSetLocalsCode(
            new_locals_identifier = makeExpressionCode(
                statement.getNewLocals()
            )
        )
    else:
        assert False, statement.__class__

    if code != code.strip():
        raise AssertionError( "Code contains leading or trailing whitespace", statement, "'%s'" % code )

    return code

def generateStatementSequenceCode( statement_sequence, context,
                                   allow_none = False ):
    # The complexity is related to frame guard types, which are also handled in
    # here.  pylint: disable=R0912

    if allow_none and statement_sequence is None:
        return None

    assert statement_sequence.isStatementsSequence(), statement_sequence

    if statement_sequence.isStatementsFrame():
        guard_mode = statement_sequence.getGuardMode()
        context.setFrameGuardMode( guard_mode )

    statements = statement_sequence.getStatements()

    codes = []

    for statement in statements:
        source_ref = statement.getSourceReference()

        if Options.shallTraceExecution():
            statement_repr = repr(statement)

            if Utils.python_version >= 300:
                statement_repr = statement_repr.encode("utf8")
            codes.append(
                Generator.getStatementTrace(
                    source_ref.getAsString(),
                    statement_repr
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

            line_code = ""
        else:
            if statement.needsLineNumber():
                line_code = Generator.getLineNumberCode(
                    source_ref = source_ref
                )
            else:
                line_code = ""

            code = generateStatementCode(
                statement = statement,
                context   = context
            )

        # Cannot happen
        assert code != "", statement

        if line_code:
            code = line_code + ";\n" + code


        statement_codes = code.split( "\n" )

        assert statement_codes[0].strip() != "", (
            "Code '%s'" % code, statement )
        assert statement_codes[-1].strip() != "", (
            "Code '%s'" % code, statement )

        codes += statement_codes

    if statement_sequence.isStatementsFrame():
        provider = statement_sequence.getParentVariableProvider()

        needs_preserve = statement_sequence.needsFrameExceptionPreversing()

        if guard_mode == "generator":
            assert provider.isExpressionFunctionBody() and \
                   provider.isGenerator()

            # TODO: This case should care about "needs_preserve", as for
            # Python3 it is actually not a stub of empty code.

            code = Generator.getFrameGuardLightCode(
                frame_identifier = provider.getCodeName(),
                code_identifier  = statement_sequence.getCodeObjectHandle(
                    context = context
                ),
                codes            = codes,
                context          = context
            )
        elif guard_mode == "pass_through":
            assert provider.isExpressionFunctionBody()

            # This case does not care about "needs_preserve", as for that kind
            # of frame, it is an empty code stub anyway.
            code = Generator.getFrameGuardVeryLightCode(
                codes = codes,
            )
        elif guard_mode == "full":
            assert provider.isExpressionFunctionBody()

            locals_code = Generator.getFrameLocalsUpdateCode(
                locals_identifier = Generator.getLoadLocalsCode(
                    context  = context,
                    provider = provider,
                    mode     = "updated"
                )
            )

            code = Generator.getFrameGuardHeavyCode(
                frame_identifier = provider.getCodeName(),
                code_identifier  = statement_sequence.getCodeObjectHandle(
                    context
                ),
                locals_code      = locals_code,
                codes            = codes,
                needs_preserve   = needs_preserve,
                context          = context
            )
        elif guard_mode == "once":
            code = Generator.getFrameGuardOnceCode(
                frame_identifier  = provider.getCodeName(),
                code_identifier   = statement_sequence.getCodeObjectHandle(
                    context = context
                ),
                locals_identifier = Generator.getLoadLocalsCode(
                    context  = context,
                    provider = provider,
                    mode     = "updated"
                ),
                codes             = codes,
                needs_preserve    = needs_preserve,
                context           = context
            )
        else:
            assert False, guard_mode

        codes = code.split( "\n" )

    assert type( codes ) is list, type( codes )

    return codes

def generateModuleCode(global_context, module, module_name, other_modules):
    assert module.isPythonModule(), module

    context = Contexts.PythonModuleContext(
        module_name    = module_name,
        code_name      = Generator.getModuleIdentifier(module_name),
        filename       = module.getFilename(),
        global_context = global_context,
        is_empty       = module.getBody() is None
    )

    statement_sequence = module.getBody()

    codes = generateStatementSequenceCode(
        statement_sequence = statement_sequence,
        allow_none         = True,
        context            = context,
    )

    codes = codes or []

    function_decl_codes = []
    function_body_codes = []
    extra_declarations = []

    for function_body in module.getUsedFunctions():
        function_code = generateFunctionBodyCode(
            function_body = function_body,
            context       = context
        )

        assert type( function_code ) is str

        function_body_codes.append( function_code )

        if function_body.needsDirectCall():
            function_decl = Generator.getFunctionDirectDecl(
                function_identifier = function_body.getCodeName(),
                closure_variables   = function_body.getClosureVariables(),
                parameter_variables = function_body.getParameters().getAllVariables(),
                file_scope          = Generator.getExportScopeCode(
                    cross_module = function_body.isCrossModuleUsed()
                )
            )

            if function_body.isCrossModuleUsed():
                extra_declarations.append( function_decl )
            else:
                function_decl_codes.append( function_decl )

    for _identifier, code in sorted( iterItems( context.getHelperCodes() ) ):
        function_body_codes.append( code )

    for _identifier, code in sorted( iterItems( context.getDeclarations() ) ):
        function_decl_codes.append( code )

    function_body_codes = "\n\n".join( function_body_codes )
    function_decl_codes = "\n\n".join( function_decl_codes )

    metapath_loader_inittab = []

    for other_module in other_modules:
        metapath_loader_inittab.append(
            Generator.getModuleMetapathLoaderEntryCode(
                module_name = other_module.getFullName(),
                is_shlib    = other_module.isPythonShlibModule()
            )
        )


    module_source_code = Generator.getModuleCode(
        module_name             = module_name,
        codes                   = codes,
        metapath_loader_inittab = metapath_loader_inittab,
        function_decl_codes     = function_decl_codes,
        function_body_codes     = function_body_codes,
        temp_variables          = module.getTempVariables(),
        context                 = context,
    )

    extra_declarations = "\n".join( extra_declarations )

    module_header_code = Generator.getModuleDeclarationCode(
        module_name        = module_name,
        extra_declarations = extra_declarations
    )

    return module_source_code, module_header_code, context


def generateMainCode(codes, context):
    return Generator.getMainCode(
        context = context,
        codes   = codes
    )

def generateConstantsDeclarationCode(context):
    return Generator.getConstantsDeclarationCode(
        context = context
    )

def generateConstantsDefinitionCode(context):
    return Generator.getConstantsDefinitionCode(
        context = context
    )


def generateHelpersCode():
    header_code = Generator.getMakeTuplesCode() + \
                  Generator.getMakeListsCode() + \
                  Generator.getMakeDictsCode() + \
                  Generator.getMakeSetsCode() + \
                  Generator.getCallsDecls()

    body_code = Generator.getCallsCode()

    return header_code, body_code

def makeGlobalContext():
    return Contexts.PythonGlobalContext()
