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
using primitives from the given generator to build code sequences (list of
strings).

As such this is the place that knows how to take a condition and two code
branches and make a code block out of it. But it doesn't contain any target
language syntax.
"""

from nuitka import Constants, Options, Tracing, Utils
from nuitka.__past__ import iterItems
from nuitka.codegen.AttributeCodes import generateAttributeLookupCode

from . import Contexts, Emission, Generator, Helpers, LineNumberCodes
from .ConditionalCodes import generateConditionCode
from .ConstantCodes import generateConstantReferenceCode
from .ErrorCodes import getErrorExitBoolCode
from .PythonAPICodes import generateCAPIObjectCode, generateCAPIObjectCode0
from .SliceCodes import generateBuiltinSliceCode
from .SubscriptCodes import generateSubscriptLookupCode
from .VariableCodes import generateVariableReferenceCode


def generateTupleCreationCode(to_name, elements, emit, context):
    if _areConstants(elements):
        Generator.getConstantAccess(
            to_name  = to_name,
            constant = tuple(
                element.getConstant() for element in elements
            ),
            emit     = emit,
            context  = context
        )
    else:
        emit(
            "%s = PyTuple_New( %d );" % (
                to_name,
                len(elements)
            )
        )

        context.addCleanupTempName(to_name)

        element_name = context.allocateTempName("tuple_element")

        for count, element in enumerate(elements):
            generateExpressionCode(
                to_name    = element_name,
                expression = element,
                emit       = emit,
                context    = context
            )

            if not context.needsCleanup(element_name):
                emit("Py_INCREF( %s );" % element_name)
            else:
                context.removeCleanupTempName(element_name)

            emit(
                "PyTuple_SET_ITEM( %s, %d, %s );" % (
                    to_name,
                    count,
                    element_name
                )
            )


def generateListCreationCode(to_name, elements, emit, context):
    if _areConstants(elements):
        assert False
    else:
        emit(
            "%s = PyList_New( %d );" % (
                to_name,
                len(elements)
            )
        )

        context.addCleanupTempName(to_name)

        element_name = context.allocateTempName("list_element")

        for count, element in enumerate(elements):
            generateExpressionCode(
                to_name    = element_name,
                expression = element,
                emit       = emit,
                context    = context
            )

            if not context.needsCleanup(element_name):
                emit("Py_INCREF( %s );" % element_name)
            else:
                context.removeCleanupTempName(element_name)

            emit(
                "PyList_SET_ITEM( %s, %d, %s );" % (
                    to_name,
                    count,
                    element_name
                )
            )


def generateSetCreationCode(to_name, elements, emit, context):
    emit(
        "%s = PySet_New( NULL );" % (
            to_name,
        )
    )

    context.addCleanupTempName(to_name)

    element_name = context.allocateTempName("set_element")

    for element in elements:
        generateExpressionCode(
            to_name    = element_name,
            expression = element,
            emit       = emit,
            context    = context
        )

        if element.isKnownToBeHashable():
            emit(
                "PySet_Add( %s, %s );" % (
                    to_name,
                    element_name
                )
            )
        else:
            res_name = context.getIntResName()

            emit(
                "%s = PySet_Add( %s, %s );" % (
                    res_name,
                    to_name,
                    element_name
                )
            )

            getErrorExitBoolCode(
                condition = "%s != 0" % res_name,
                emit      = emit,
                context   = context
            )

        if context.needsCleanup(element_name):
            emit("Py_DECREF( %s );" % element_name)
            context.removeCleanupTempName(element_name)


def generateDictionaryCreationCode(to_name, pairs, emit, context):
    if Options.isFullCompat() and Utils.python_version >= 340:
        return _generateDictionaryCreationCode340(
            to_name = to_name,
            pairs   = pairs,
            emit    = emit,
            context = context
        )
    else:
        return _generateDictionaryCreationCode(
            to_name = to_name,
            pairs   = pairs,
            emit    = emit,
            context = context
        )


def _generateDictionaryCreationCode340(to_name, pairs, emit, context):

    # Note: This is only for Python3.4 full compatibility, it's worse than for
    # the other versions, and only to be used if that level of compatibility is
    # requested. It is to avoid changes in dictionary items order that are
    # normal with random hashing.

    emit(
        "%s = _PyDict_NewPresized( %d );" % (
            to_name,
            len(pairs)
        )
    )

    context.addCleanupTempName(to_name)

    dict_key_names = []
    dict_value_names = []
    keys = []

    # Strange as it is, CPython evaluates the key/value pairs strictly in order,
    # but for each pair, the value first.
    for pair in pairs:
        dict_key_name = context.allocateTempName("dict_key")
        dict_value_name = context.allocateTempName("dict_value")

        generateExpressionCode(
            to_name    = dict_value_name,
            expression = pair.getValue(),
            emit       = emit,
            context    = context
        )

        generateExpressionCode(
            to_name    = dict_key_name,
            expression = pair.getKey(),
            emit       = emit,
            context    = context
        )

        dict_key_names.append(dict_key_name)
        dict_value_names.append(dict_value_name)

        keys.append(pair.getKey())

    for key, dict_key_name, dict_value_name in \
      zip(reversed(keys), reversed(dict_key_names), reversed(dict_value_names)):
        if key.isKnownToBeHashable():
            emit(
                "PyDict_SetItem( %s, %s, %s );" % (
                    to_name,
                    dict_key_name,
                    dict_value_name
                )
            )
        else:
            res_name = context.getIntResName()

            emit(
                "%s = PyDict_SetItem( %s, %s, %s );" % (
                    res_name,
                    to_name,
                    dict_key_name,
                    dict_value_name
                )
            )

            getErrorExitBoolCode(
                condition = "%s != 0" % res_name,
                emit      = emit,
                context   = context
            )

        if context.needsCleanup(dict_value_name):
            emit("Py_DECREF( %s );" % dict_value_name)
            context.removeCleanupTempName(dict_value_name)

        if context.needsCleanup(dict_key_name):
            emit("Py_DECREF( %s );" % dict_key_name)
            context.removeCleanupTempName(dict_key_name)


def _generateDictionaryCreationCode(to_name, pairs, emit, context):
    emit(
        "%s = _PyDict_NewPresized( %d );" % (
            to_name,
            len(pairs)
        )
    )

    context.addCleanupTempName(to_name)

    # Strange as it is, CPython evaluates the key/value pairs strictly in order,
    # but for each pair, the value first.
    for pair in pairs:
        dict_key_name = context.allocateTempName("dict_key")
        dict_value_name = context.allocateTempName("dict_value")

        generateExpressionCode(
            to_name    = dict_value_name,
            expression = pair.getValue(),
            emit       = emit,
            context    = context
        )

        key = pair.getKey()

        generateExpressionCode(
            to_name    = dict_key_name,
            expression = key,
            emit       = emit,
            context    = context
        )


        if key.isKnownToBeHashable():
            emit(
                "PyDict_SetItem( %s, %s, %s );" % (
                    to_name,
                    dict_key_name,
                    dict_value_name
                )
            )
        else:
            res_name = context.getIntResName()

            emit(
                "%s = PyDict_SetItem( %s, %s, %s );" % (
                    res_name,
                    to_name,
                    dict_key_name,
                    dict_value_name
                )
            )

            getErrorExitBoolCode(
                condition = "%s != 0" % res_name,
                emit      = emit,
                context   = context
            )

        if context.needsCleanup(dict_value_name):
            emit("Py_DECREF( %s );" % dict_value_name)
            context.removeCleanupTempName(dict_value_name)

        if context.needsCleanup(dict_key_name):
            emit("Py_DECREF( %s );" % dict_key_name)
            context.removeCleanupTempName(dict_key_name)



def generateFunctionCallCode(to_name, call_node, emit, context):
    assert call_node.getFunction().isExpressionFunctionCreation()

    function_body = call_node.getFunction().getFunctionRef().getFunctionBody()
    function_identifier = function_body.getCodeName()

    argument_values = call_node.getArgumentValues()

    arg_names = []
    for count, arg_value in enumerate(argument_values):
        arg_name = context.allocateTempName("dircall_arg%d" % (count+1))

        generateExpressionCode(
            to_name    = arg_name,
            expression = arg_value,
            emit       = emit,
            context    = context
        )

        arg_names.append(arg_name)

    Generator.getDirectFunctionCallCode(
        to_name             = to_name,
        function_identifier = function_identifier,
        arg_names           = arg_names,
        closure_variables   = function_body.getClosureVariables(),
        emit                = emit,
        context             = context
    )

_generated_functions = {}



def generateFunctionCreationCode(to_name, function_body, defaults, kw_defaults,
                                  annotations, defaults_first, emit, context):
    # This is about creating functions, which is detail ridden stuff,
    # pylint: disable=R0914

    assert function_body.needsCreation(), function_body

    parameters = function_body.getParameters()

    def handleKwDefaults():
        if kw_defaults:
            kw_defaults_name = context.allocateTempName("kw_defaults")

            assert not kw_defaults.isExpressionConstantRef() or \
                   not kw_defaults.getConstant() == {}, kw_defaults.getConstant()

            generateExpressionCode(
                to_name    = kw_defaults_name,
                expression = kw_defaults,
                emit       = emit,
                context    = context
            )
        else:
            kw_defaults_name = None

        return kw_defaults_name

    def handleDefaults():
        if defaults:
            defaults_name = context.allocateTempName("defaults")

            generateTupleCreationCode(
                to_name  = defaults_name,
                elements = defaults,
                emit     = emit,
                context  = context
            )
        else:
            defaults_name = None

        return defaults_name

    if defaults_first:
        defaults_name = handleDefaults()
        kw_defaults_name = handleKwDefaults()
    else:
        kw_defaults_name = handleKwDefaults()
        defaults_name = handleDefaults()

    if annotations:
        annotations_name = context.allocateTempName("annotations")

        generateExpressionCode(
            to_name    = annotations_name,
            expression = annotations,
            emit       = emit,
            context    = context,
        )
    else:
        annotations_name = None

    function_identifier = function_body.getCodeName()

    maker_code = Generator.getFunctionMakerCode(
        function_name       = function_body.getFunctionName(),
        function_qualname   = function_body.getFunctionQualname(),
        function_identifier = function_identifier,
        parameters          = parameters,
        local_variables     = function_body.getLocalVariables(),
        closure_variables   = function_body.getClosureVariables(),
        defaults_name       = defaults_name,
        kw_defaults_name    = kw_defaults_name,
        annotations_name    = annotations_name,
        source_ref          = function_body.getSourceReference(),
        function_doc        = function_body.getDoc(),
        is_generator        = function_body.isGenerator(),
        is_optimized        = not function_body.needsLocalsDict(),
        context             = context
    )

    context.addHelperCode(function_identifier, maker_code)

    function_decl = Generator.getFunctionMakerDecl(
        function_identifier = function_body.getCodeName(),
        defaults_name       = defaults_name,
        kw_defaults_name    = kw_defaults_name,
        annotations_name    = annotations_name,
        closure_variables   = function_body.getClosureVariables()
    )

    if function_body.getClosureVariables() and not function_body.isGenerator():
        function_decl += "\n"

        function_decl += Generator.getFunctionContextDefinitionCode(
            function_identifier = function_body.getCodeName(),
            closure_variables   = function_body.getClosureVariables(),
        )

    context.addDeclaration(function_identifier, function_decl)

    Generator.getFunctionCreationCode(
        to_name             = to_name,
        function_identifier = function_body.getCodeName(),
        defaults_name       = defaults_name,
        kw_defaults_name    = kw_defaults_name,
        annotations_name    = annotations_name,
        closure_variables   = function_body.getClosureVariables(),
        emit                = emit,
        context             = context
    )

    Generator.getReleaseCode(
        release_name = annotations_name,
        emit         = emit,
        context      = context
    )

    Generator.getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )


def generateFunctionBodyCode(function_body, context):
    function_identifier = function_body.getCodeName()

    if function_identifier in _generated_functions:
        return _generated_functions[function_identifier]

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
    function_codes = []

    generateStatementSequenceCode(
        statement_sequence = function_body.getBody(),
        allow_none         = True,
        emit               = function_codes.append,
        context            = function_context
    )

    parameters = function_body.getParameters()

    needs_exception_exit = function_body.mayRaiseException(BaseException)
    needs_generator_return = function_body.needsGeneratorReturnExit()

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
            function_doc           = function_body.getDoc(),
            needs_exception_exit   = needs_exception_exit,
            needs_generator_return = needs_generator_return
        )
    else:
        function_code = Generator.getFunctionCode(
            context              = function_context,
            function_name        = function_body.getFunctionName(),
            function_identifier  = function_identifier,
            parameters           = parameters,
            closure_variables    = function_body.getClosureVariables(),
            user_variables       = function_body.getUserLocalVariables(),
            temp_variables       = function_body.getTempVariables(),
            function_codes       = function_codes,
            function_doc         = function_body.getDoc(),
            needs_exception_exit = needs_exception_exit,
            file_scope           = Generator.getExportScopeCode(
                cross_module = function_body.isCrossModuleUsed()
            )
        )

    return function_code


def generateComparisonExpressionCode(to_name, comparison_expression, emit,
                                     context):
    left_name = context.allocateTempName("compexpr_left")
    right_name = context.allocateTempName("compexpr_right")

    generateExpressionCode(
        to_name    = left_name,
        expression = comparison_expression.getLeft(),
        emit       = emit,
        context    = context
    )
    generateExpressionCode(
        to_name    = right_name,
        expression = comparison_expression.getRight(),
        emit       = emit,
        context    = context
    )

    Generator.getComparisonExpressionCode(
        to_name    = to_name,
        comparator = comparison_expression.getComparator(),
        left_name  = left_name,
        right_name = right_name,
        emit       = emit,
        context    = context
    )


def _areConstants(expressions):
    for expression in expressions:
        if not expression.isExpressionConstantRef():
            return False

        if expression.isMutable():
            return False
    return True


def generateSliceRangeIdentifier(lower, upper, scope, emit, context):
    lower_name = context.allocateTempName(
        scope + "slicedel_index_lower",
        "Py_ssize_t"
    )
    upper_name = context.allocateTempName(
        scope + "_index_upper",
        "Py_ssize_t"
    )

    def isSmallNumberConstant(node):
        value = node.getConstant()

        if Constants.isNumberConstant(value):
            return abs(int(value)) < 2**63-1
        else:
            return False

    if lower is None:
        Generator.getMinIndexCode(
            to_name = lower_name,
            emit    = emit
        )
    elif lower.isExpressionConstantRef() and isSmallNumberConstant(lower):
        Generator.getIndexValueCode(
            to_name = lower_name,
            value   = int(lower.getConstant()),
            emit    = emit
        )
    else:
        value_name = context.allocateTempName(scope + "_lower_index_value")

        generateExpressionCode(
            to_name    = value_name,
            expression = lower,
            emit       = emit,
            context    = context
        )

        Generator.getIndexCode(
            to_name    = lower_name,
            value_name = value_name,
            emit       = emit,
            context    = context
        )

    if upper is None:
        Generator.getMaxIndexCode(
            to_name = upper_name,
            emit    = emit
        )
    elif upper.isExpressionConstantRef() and isSmallNumberConstant(upper):
        Generator.getIndexValueCode(
            to_name = upper_name,
            value   = int(upper.getConstant()),
            emit    = emit
        )
    else:
        value_name = context.allocateTempName(scope + "_upper_index_value")

        generateExpressionCode(
            to_name    = value_name,
            expression = upper,
            emit       = emit,
            context    = context
        )

        Generator.getIndexCode(
            to_name    = upper_name,
            value_name = value_name,
            emit       = emit,
            context    = context
        )

    return lower_name, upper_name

def _decideSlicing(lower, upper):
    return (lower is None or lower.isIndexable()) and \
           (upper is None or upper.isIndexable())


def generateSliceLookupCode(to_name, expression, emit, context):
    assert Utils.python_version < 300

    lower = expression.getLower()
    upper = expression.getUpper()

    if _decideSlicing(lower, upper):
        lower_name, upper_name = generateSliceRangeIdentifier(
            lower   = lower,
            upper   = upper,
            scope   = "slice",
            emit    = emit,
            context = context
        )

        source_name = context.allocateTempName("slice_source")

        generateExpressionCode(
            to_name    = source_name,
            expression = expression.getLookupSource(),
            emit       = emit,
            context    = context
        )

        Generator.getSliceLookupIndexesCode(
            to_name     = to_name,
            source_name = source_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            emit        = emit,
            context     = context
        )
    else:
        source_name, lower_name, upper_name = generateExpressionsCode(
            names       = ("slice_source", "slice_lower", "slice_upper"),
            expressions = (
                expression.getLookupSource(),
                expression.getLower(),
                expression.getUpper()
            ),
            emit        = emit,
            context     = context
        )

        Generator.getSliceLookupCode(
            to_name     = to_name,
            source_name = source_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            emit        = emit,
            context     = context
        )


def generateCallCode(to_name, call_node, emit, context):
    # There is a whole lot of different cases, for each of which, we create
    # optimized code, constant, with and without positional or keyword args
    # each, so there is lots of branches here, pylint: disable=R0912

    called_name = context.allocateTempName("called")

    generateExpressionCode(
        to_name    = called_name,
        expression = call_node.getCalled(),
        emit       = emit,
        context    = context
    )

    call_args = call_node.getCallArgs()
    call_kw = call_node.getCallKw()

    if call_kw.isExpressionConstantRef() and call_kw.getConstant() == {}:
        if call_args.isExpressionMakeTuple():
            call_arg_names = []

            for call_arg_element in call_args.getElements():
                call_arg_name = context.allocateTempName("call_arg_element")

                generateExpressionCode(
                    to_name    = call_arg_name,
                    expression = call_arg_element,
                    emit       = emit,
                    context    = context,
                )

                call_arg_names.append(call_arg_name)

            assert call_arg_names

            if Options.isFullCompat():
                context.setCurrentSourceCodeReference(
                    call_args.getElements()[-1].getSourceReference()
                )

            Generator.getCallCodePosArgsQuick(
                to_name     = to_name,
                called_name = called_name,
                arg_names   = call_arg_names,
                emit        = emit,
                context     = context
            )
        elif call_args.isExpressionConstantRef():
            call_args_value = call_args.getConstant()
            assert type(call_args_value) is tuple

            call_arg_names = []

            for call_arg_element in call_args_value:
                call_arg_name = context.allocateTempName("call_arg_element")

                Generator.getConstantAccess(
                    to_name  = call_arg_name,
                    constant = call_arg_element,
                    emit     = emit,
                    context  = context,
                )

                call_arg_names.append(call_arg_name)

            if Options.isFullCompat():
                context.setCurrentSourceCodeReference(
                    call_args.getSourceReference()
                )

            if call_arg_names:
                Generator.getCallCodePosArgsQuick(
                    to_name     = to_name,
                    called_name = called_name,
                    arg_names   = call_arg_names,
                    emit        = emit,
                    context     = context
                )
            else:
                Generator.getCallCodeNoArgs(
                    to_name     = to_name,
                    called_name = called_name,
                    emit        = emit,
                    context     = context
                )
        else:
            args_name = context.allocateTempName("call_pos")

            generateExpressionCode(
                to_name    = args_name,
                expression = call_args,
                emit       = emit,
                context    = context
            )

            if Options.isFullCompat():
                context.setCurrentSourceCodeReference(call_args.getSourceReference())

            Generator.getCallCodePosArgs(
                to_name     = to_name,
                called_name = called_name,
                args_name   = args_name,
                emit        = emit,
                context     = context
            )
    else:
        if call_args.isExpressionConstantRef() and \
           call_args.getConstant() == ():
            call_kw_name = context.allocateTempName("call_kw")

            generateExpressionCode(
                to_name    = call_kw_name,
                expression = call_kw,
                emit       = emit,
                context    = context
            )

            if Options.isFullCompat():
                context.setCurrentSourceCodeReference(
                    call_kw.getSourceReference()
                )

            Generator.getCallCodeKeywordArgs(
                to_name      = to_name,
                called_name  = called_name,
                call_kw_name = call_kw_name,
                emit         = emit,
                context      = context
            )
        else:
            call_args_name = context.allocateTempName("call_pos")

            generateExpressionCode(
                to_name    = call_args_name,
                expression = call_args,
                emit       = emit,
                context    = context
            )

            call_kw_name = context.allocateTempName("call_kw")

            generateExpressionCode(
                to_name    = call_kw_name,
                expression = call_kw,
                emit       = emit,
                context    = context
            )

            if Options.isFullCompat():
                context.setCurrentSourceCodeReference(
                    call_kw.getSourceReference()
                )

            Generator.getCallCodePosKeywordArgs(
                to_name        = to_name,
                called_name    = called_name,
                call_args_name = call_args_name,
                call_kw_name   = call_kw_name,
                emit           = emit,
                context        = context
            )


def generateBuiltinLocalsCode(to_name, locals_node, emit, context):
    provider = locals_node.getParentVariableProvider()

    return Generator.getLoadLocalsCode(
        to_name  = to_name,
        provider = provider,
        mode     = provider.getLocalsMode(),
        emit     = emit,
        context  = context
    )

def _generateExpressionCode(to_name, expression, emit, context, allow_none):
    # This is a dispatching function with a branch per expression node type, and
    # therefore many statements even if every branch is relatively small.
    # pylint: disable=R0912,R0915,R0914

    if expression is None and allow_none:
        return None

    # Make sure we don't generate code twice for any node, this uncovers bugs
    # where nodes are shared in the tree, which is not allowed.
    assert not hasattr(expression, "code_generated"), expression
    expression.code_generated = True

    old_source_ref = context.setCurrentSourceCodeReference(expression.getSourceReference())

    def makeExpressionCode(to_name, expression, allow_none = False):
        if allow_none and expression is None:
            return None

        generateExpressionCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context
        )

    if not expression.isExpression():
        Tracing.printError("No expression %r" % expression)

        expression.dump()
        assert False, expression

    res = Helpers.generateExpressionCode(
        to_name    = to_name,
        expression = expression,
        emit       = emit,
        context    = context
    )

    if res:
        pass
    elif expression.isExpressionSliceLookup():
        generateSliceLookupCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionSliceObject():
        lower_name, upper_name, step_name = generateExpressionsCode(
            expressions = (
                expression.getLower(),
                expression.getUpper(),
                expression.getStep()
            ),
            names       = (
                "sliceobj_lower", "sliceobj_upper", "sliceobj_step"
            ),
            emit        = emit,
            context     = context
        )

        Generator.getSliceObjectCode(
            to_name    = to_name,
            lower_name = lower_name,
            upper_name = upper_name,
            step_name  = step_name,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionCall():
        generateCallCode(
            to_name   = to_name,
            call_node = expression,
            emit      = emit,
            context   = context
        )
    elif expression.isExpressionFunctionCall():
        generateFunctionCallCode(
            to_name   = to_name,
            call_node = expression,
            emit      = emit,
            context   = context
        )
    elif expression.isExpressionBuiltinNext1():
        value_name = context.allocateTempName("next1_arg")

        makeExpressionCode(
            to_name    = value_name,
            expression = expression.getValue()
        )

        Generator.getBuiltinNext1Code(
            to_name = to_name,
            value   = value_name,
            emit    = emit,
            context = context
        )
    elif expression.isExpressionBuiltinNext2():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_NEXT2",
            arg_desc = (
                ("next_arg", expression.getIterator()),
                ("next_default", expression.getDefault()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionSpecialUnpack():
        value_name = context.allocateTempName("unpack")

        makeExpressionCode(
            to_name    = value_name,
            expression = expression.getValue()
        )

        Generator.getUnpackNextCode(
            to_name = to_name,
            value   = value_name,
            count   = expression.getCount(),
            emit    = emit,
            context = context
        )
    elif expression.isExpressionBuiltinGlobals():
        Generator.getLoadGlobalsCode(
            to_name = to_name,
            emit    = emit,
            context = context
        )
    elif expression.isExpressionImportModule():
        generateImportModuleCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinImport():
        generateBuiltinImportCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionImportModuleHard():
        Generator.getImportModuleHardCode(
            to_name     = to_name,
            module_name = expression.getModuleName(),
            import_name = expression.getImportName(),
            emit        = emit,
            context     = context
        )
    elif expression.isExpressionFunctionCreation():
        generateFunctionCreationCode(
            to_name        = to_name,
            function_body  = expression.getFunctionRef().getFunctionBody(),
            defaults       = expression.getDefaults(),
            kw_defaults    = expression.getKwDefaults(),
            annotations    = expression.getAnnotations(),
            defaults_first = not expression.kw_defaults_before_defaults,
            emit           = emit,
            context        = context
        )
    elif expression.isExpressionCaughtExceptionTypeRef():
        Generator.getExceptionCaughtTypeCode(
            to_name = to_name,
            emit    = emit,
            context = context
        )
    elif expression.isExpressionCaughtExceptionValueRef():
        Generator.getExceptionCaughtValueCode(
            to_name = to_name,
            emit    = emit,
            context = context
        )
    elif expression.isExpressionCaughtExceptionTracebackRef():
        Generator.getExceptionCaughtTracebackCode(
            to_name = to_name,
            emit    = emit,
            context = context
        )
    elif expression.isExpressionBuiltinExceptionRef():
        Generator.getExceptionRefCode(
            to_name        = to_name,
            exception_type = expression.getExceptionName(),
            emit           = emit,
            context        = context
        )
    elif expression.isExpressionBuiltinAnonymousRef():
        Generator.getBuiltinAnonymousRefCode(
            to_name      = to_name,
            builtin_name = expression.getBuiltinName(),
            emit         = emit
        )
    elif expression.isExpressionBuiltinMakeException():
        exception_arg_names = []

        for exception_arg in expression.getArgs():
            exception_arg_name = context.allocateTempName("make_exception_arg")

            makeExpressionCode(
                to_name    = exception_arg_name,
                expression = exception_arg
            )

            exception_arg_names.append(exception_arg_name)

        Generator.getMakeBuiltinExceptionCode(
            to_name        = to_name,
            exception_type = expression.getExceptionName(),
            arg_names      = exception_arg_names,
            emit           = emit,
            context        = context
        )
    elif expression.isExpressionOperationBinary():
        left_arg_name = context.allocateTempName("binop_left")
        right_arg_name = context.allocateTempName("binop_right")

        makeExpressionCode(
            to_name    = left_arg_name,
            expression = expression.getLeft()
        )
        makeExpressionCode(
            to_name    = right_arg_name,
            expression = expression.getRight()
        )

        Generator.getOperationCode(
            to_name   = to_name,
            operator  = expression.getOperator(),
            arg_names = (left_arg_name, right_arg_name),
            emit      = emit,
            context   = context
        )
    elif expression.isExpressionOperationUnary():
        arg_name = context.allocateTempName("unary_arg")

        makeExpressionCode(
            to_name    = arg_name,
            expression = expression.getOperand()
        )

        Generator.getOperationCode(
            to_name   = to_name,
            operator  = expression.getOperator(),
            arg_names = (arg_name,),
            emit      = emit,
            context   = context
        )
    elif expression.isExpressionComparison():
        generateComparisonExpressionCode(
            to_name               = to_name,
            comparison_expression = expression,
            emit                  = emit,
            context               = context
        )
    elif Utils.python_version < 300 and expression.isExpressionBuiltinStr():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "PyObject_Str",
            arg_desc = (
                ("str_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif (
           Utils.python_version < 300 and \
           expression.isExpressionBuiltinUnicode()
        ) or (
           Utils.python_version >= 300 and \
           expression.isExpressionBuiltinStr()
        ):
        encoding = expression.getEncoding()
        errors = expression.getErrors()

        if encoding is None and errors is None:
            generateCAPIObjectCode(
                to_name  = to_name,
                capi     = "PyObject_Unicode",
                arg_desc = (
                    (
                        "str_arg" if Utils.python_version < 300 \
                          else "unicode_arg",
                        expression.getValue()
                    ),
                ),
                emit     = emit,
                context  = context
            )
        else:
            generateCAPIObjectCode(
                to_name   = to_name,
                capi      = "TO_UNICODE3",
                arg_desc  = (
                    ("unicode_arg", expression.getValue()),
                    ("unicode_encoding", encoding),
                    ("unicode_errors", errors),
                ),
                emit      = emit,
                none_null = True,
                context   = context
            )

    elif expression.isExpressionBuiltinIter1():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "MAKE_ITERATOR",
            arg_desc = (
                ("iter_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinIter2():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_ITER2",
            arg_desc = (
                ("iter_callable", expression.getCallable()),
                ("iter_sentinel", expression.getSentinel()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinType1():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_TYPE1",
            arg_desc = (
                ("type_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinIsinstance():
        generateCAPIObjectCode0(
            to_name  = to_name,
            capi     = "BUILTIN_ISINSTANCE",
            arg_desc = (
                ("isinstance_inst", expression.getInstance()),
                ("isinstance_cls", expression.getCls()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionSpecialAttributeLookup():
        source_name = context.allocateTempName("attr_source")

        makeExpressionCode(
            to_name    = source_name,
            expression = expression.getLookupSource()
        )


        Generator.getSpecialAttributeLookupCode(
            to_name     = to_name,
            source_name = source_name,
            attr_name   = Generator.getConstantCode(
                context  = context,
                constant = expression.getAttributeName()
            ),
            emit        = emit,
            context     = context
        )
    elif expression.isExpressionBuiltinHasattr():
        generateCAPIObjectCode0(
            to_name  = to_name,
            capi     = "BUILTIN_HASATTR",
            arg_desc = (
                ("hasattr_value", expression.getLookupSource()),
                ("hasattr_attr", expression.getAttribute()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinGetattr():
        generateCAPIObjectCode(
            to_name   = to_name,
            capi      = "BUILTIN_GETATTR",
            arg_desc  = (
                ("getattr_target", expression.getLookupSource()),
                ("getattr_attr", expression.getAttribute()),
                ("getattr_default", expression.getDefault()),
            ),
            emit      = emit,
            none_null = True,
            context   = context
        )
    elif expression.isExpressionBuiltinSetattr():
        generateCAPIObjectCode0(
            to_name  = to_name,
            capi     = "BUILTIN_SETATTR",
            arg_desc = (
                ("setattr_target", expression.getLookupSource()),
                ("setattr_attr", expression.getAttribute()),
                ("setattr_value", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinRef():
        Generator.getBuiltinRefCode(
            to_name      = to_name,
            builtin_name = expression.getBuiltinName(),
            emit         = emit,
            context      = context
        )
    elif expression.isExpressionBuiltinOriginalRef():
        assert not expression.isExpressionBuiltinRef()

        # This is not implemented currently, but ought to be one day.
        assert False
    elif expression.isExpressionMakeTuple():
        generateTupleCreationCode(
            to_name  = to_name,
            elements = expression.getElements(),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionMakeList():
        generateListCreationCode(
            to_name  = to_name,
            elements = expression.getElements(),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionMakeSet():
        generateSetCreationCode(
            to_name  = to_name,
            elements = expression.getElements(),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionMakeDict():
        assert expression.getPairs()

        generateDictionaryCreationCode(
            to_name = to_name,
            pairs   = expression.getPairs(),
            emit    = emit,
            context = context
        )
    elif expression.isExpressionBuiltinInt():
        value = expression.getValue()
        base = expression.getBase()

        assert value is not None

        if base is None:
            generateCAPIObjectCode(
                to_name  = to_name,
                capi     = "PyNumber_Int",
                arg_desc = (
                    ("int_arg", value),
                ),
                emit     = emit,
                context  = context
            )
        else:
            value_name = context.allocateTempName("int_value")

            makeExpressionCode(
                to_name    = value_name,
                expression = value
            )

            base_name = context.allocateTempName("int_base")

            makeExpressionCode(
                to_name    = base_name,
                expression = base
            )

            Generator.getBuiltinInt2Code(
                to_name    = to_name,
                base_name  = base_name,
                value_name = value_name,
                emit       = emit,
                context    = context
            )
    elif Utils.python_version < 300 and expression.isExpressionBuiltinLong():
        value = expression.getValue()
        base = expression.getBase()

        assert value is not None

        if base is None:
            generateCAPIObjectCode(
                to_name  = to_name,
                capi     = "PyNumber_Long",
                arg_desc = (
                    ("long_arg", value),
                ),
                emit     = emit,
                context  = context
            )
        else:
            value_name = context.allocateTempName("long_value")

            makeExpressionCode(
                to_name    = value_name,
                expression = value
            )

            base_name = context.allocateTempName("long_base")

            makeExpressionCode(
                to_name    = base_name,
                expression = base
            )

            Generator.getBuiltinLong2Code(
                to_name    = to_name,
                base_name  = base_name,
                value_name = value_name,
                emit       = emit,
                context    = context
            )
    elif expression.isExpressionImportName():
        from_arg_name = context.allocateTempName("import_name_from")

        makeExpressionCode(
            to_name    = from_arg_name,
            expression = expression.getModule()
        )

        Generator.getImportNameCode(
            to_name       = to_name,
            import_name   = expression.getImportName(),
            from_arg_name = from_arg_name,
            emit          = emit,
            context       = context
        )
    elif expression.isExpressionConditional():
        true_target = context.allocateLabel("condexpr_true")
        false_target = context.allocateLabel("condexpr_false")
        end_target = context.allocateLabel("condexpr_end")

        old_true_target = context.getTrueBranchTarget()
        old_false_target = context.getFalseBranchTarget()

        context.setTrueBranchTarget(true_target)
        context.setFalseBranchTarget(false_target)

        generateConditionCode(
            condition = expression.getCondition(),
            emit      = emit,
            context   = context
        )

        Generator.getLabelCode(true_target,emit)
        makeExpressionCode(
            to_name    = to_name,
            expression = expression.getExpressionYes()
        )
        needs_ref1 = context.needsCleanup(to_name)

        # Must not clean this up in other expression.
        if needs_ref1:
            context.removeCleanupTempName(to_name)

        real_emit = emit
        emit = Emission.SourceCodeCollector()

        makeExpressionCode(
            to_name    = to_name,
            expression = expression.getExpressionNo()
        )

        needs_ref2 = context.needsCleanup(to_name)

        # TODO: Need to buffer generated code, so we can emit extra reference if
        # not same.
        if needs_ref1 and not needs_ref2:
            Generator.getGotoCode(end_target, real_emit)
            Generator.getLabelCode(false_target, real_emit)

            for line in emit.codes:
                real_emit(line)
            emit = real_emit

            emit("Py_INCREF( %s );" % to_name)
            context.addCleanupTempName(to_name)
        elif not needs_ref1 and needs_ref2:
            real_emit("Py_INCREF( %s );" % to_name)
            Generator.getGotoCode(end_target, real_emit)
            Generator.getLabelCode(false_target, real_emit)

            for line in emit.codes:
                real_emit(line)
            emit = real_emit
        else:
            Generator.getGotoCode(end_target, real_emit)
            Generator.getLabelCode(false_target, real_emit)

            for line in emit.codes:
                real_emit(line)
            emit = real_emit

        Generator.getLabelCode(end_target,emit)

        context.setTrueBranchTarget(old_true_target)
        context.setFalseBranchTarget(old_false_target)
    elif expression.isExpressionDictOperationGet():
        dict_name, key_name = generateExpressionsCode(
            expressions = (
                expression.getDict(),
                expression.getKey()
            ),
            names       = ("dget_dict", "dget_key"),
            emit        = emit,
            context     = context
        )

        Generator.getDictOperationGetCode(
            to_name   = to_name,
            dict_name = dict_name,
            key_name  = key_name,
            emit      = emit,
            context   = context
        )
    elif expression.isExpressionListOperationAppend():
        list_name, value_name = generateExpressionsCode(
            expressions = (
                expression.getList(),
                expression.getValue()
            ),
            names       = ("append_to", "append_value"),
            emit        = emit,
            context     = context
        )

        Generator.getListOperationAppendCode(
            to_name    = to_name,
            list_name  = list_name,
            value_name = value_name,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionSetOperationAdd():
        set_name, value_name = generateExpressionsCode(
            expressions = (
                expression.getSet(),
                expression.getValue()
            ),
            names       = ("setadd_to", "setadd_value"),
            emit        = emit,
            context     = context
        )

        Generator.getSetOperationAddCode(
            to_name    = to_name,
            set_name   = set_name,
            value_name = value_name,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionDictOperationSet():
        dict_name, key_name, value_name = generateExpressionsCode(
            expressions = (
                expression.getDict(),
                expression.getKey(),
                expression.getValue()
            ),
            names       = ("dictset_to", "dictset_key", "dictset_value"),
            emit        = emit,
            context     = context
        )

        Generator.getDictOperationSetCode(
            to_name    = to_name,
            dict_name  = dict_name,
            key_name   = key_name,
            value_name = value_name,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionSelectMetaclass():
        if expression.getMetaclass() is not None:
            metaclass_name = context.allocateTempName("class_meta")

            makeExpressionCode(
                to_name    = metaclass_name,
                expression = expression.getMetaclass()
            )
        else:
            metaclass_name = None

        bases_name = context.allocateTempName("class_bases")
        makeExpressionCode(
            to_name    = bases_name,
            expression = expression.getBases()
        )

        Generator.getSelectMetaclassCode(
            to_name        = to_name,
            metaclass_name = metaclass_name,
            bases_name     = bases_name,
            emit           = emit,
            context        = context
        )
    elif expression.isExpressionBuiltinLocals():
        generateBuiltinLocalsCode(
            to_name     = to_name,
            locals_node = expression,
            emit        = emit,
            context     = context
        )
    elif expression.isExpressionBuiltinDir1():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "PyObject_Dir",
            arg_desc = (
                ("dir_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinVars():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "LOOKUP_VARS",
            arg_desc = (
                ("vars_arg", expression.getSource()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinOpen():
        generateCAPIObjectCode(
            to_name   = to_name,
            capi      = "BUILTIN_OPEN",
            arg_desc  = (
                ("open_filename", expression.getFilename()),
                ("open_mode", expression.getMode()),
                ("open_buffering", expression.getBuffering()),
            ),
            none_null = True,
            emit      = emit,
            context   = context
        )
    elif expression.isExpressionBuiltinRange1():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_RANGE",
            arg_desc = (
                ("range_arg", expression.getLow()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinRange2():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_RANGE2",
            arg_desc = (
                ("range2_low", expression.getLow()),
                ("range2_high", expression.getHigh()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinRange3():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_RANGE3",
            arg_desc = (
                ("range3_low", expression.getLow()),
                ("range3_high", expression.getHigh()),
                ("range3_step", expression.getStep()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinXrange():
        generateCAPIObjectCode(
            to_name   = to_name,
            capi      = "BUILTIN_XRANGE",
            arg_desc  = (
                ("xrange_low", expression.getLow()),
                ("xrange_high", expression.getHigh()),
                ("xrange_step", expression.getStep()),
            ),
            emit      = emit,
            none_null = True,
            context   = context
        )
    elif expression.isExpressionBuiltinFloat():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "TO_FLOAT",
            arg_desc = (
                ("float_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinBool():
        generateCAPIObjectCode0(
            to_name  = to_name,
            capi     = "TO_BOOL",
            arg_desc = (
                ("bool_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinChr():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_CHR",
            arg_desc = (
                ("chr_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinOrd():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_ORD",
            arg_desc = (
                ("ord_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinBin():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_BIN",
            arg_desc = (
                ("bin_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinOct():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_OCT",
            arg_desc = (
                ("oct_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinHex():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_HEX",
            arg_desc = (
                ("hex_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinLen():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_LEN",
            arg_desc = (
                ("len_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinTuple():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "PySequence_Tuple",
            arg_desc = (
                ("tuple_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinList():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "PySequence_List",
            arg_desc = (
                ("list_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinDict():
        if expression.getPositionalArgument():
            seq_name = context.allocateTempName("dict_seq")

            makeExpressionCode(
                to_name    = seq_name,
                expression = expression.getPositionalArgument(),
                allow_none = True
            )
        else:
            seq_name = None

        if expression.getNamedArgumentPairs():
            # If there is no sequence to mix in, then directly generate
            # into to_name.

            if seq_name is None:
                generateDictionaryCreationCode(
                    to_name = to_name,
                    pairs   = expression.getNamedArgumentPairs(),
                    emit    = emit,
                    context = context
                )

                dict_name = None
            else:
                dict_name = context.allocateTempName("dict_arg")

                generateDictionaryCreationCode(
                    to_name = dict_name,
                    pairs   = expression.getNamedArgumentPairs(),
                    emit    = emit,
                    context = context
                )
        else:
            dict_name = None

        if seq_name is not None:
            Generator.getBuiltinDict2Code(
                to_name   = to_name,
                seq_name  = seq_name,
                dict_name = dict_name,
                emit      = emit,
                context   = context
            )
    elif expression.isExpressionBuiltinSet():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "PySet_New",
            arg_desc = (
                ("set_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinType3():
        type_name = context.allocateTempName("type_name")
        bases_name = context.allocateTempName("type_bases")
        dict_name = context.allocateTempName("type_dict")

        makeExpressionCode(
            to_name    = type_name,
            expression = expression.getTypeName()
        )
        makeExpressionCode(
            to_name    = bases_name,
            expression = expression.getBases()
        )
        makeExpressionCode(
            to_name    = dict_name,
            expression = expression.getDict()
        )

        Generator.getBuiltinType3Code(
            to_name    = to_name,
            type_name  = type_name,
            bases_name = bases_name,
            dict_name  = dict_name,
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionBuiltinBytearray():
        generateCAPIObjectCode(
            to_name  = to_name,
            capi     = "BUILTIN_BYTEARRAY",
            arg_desc = (
                ("bytearray_arg", expression.getValue()),
            ),
            emit     = emit,
            context  = context
        )
    elif expression.isExpressionBuiltinSuper():
        type_name, object_name = generateExpressionsCode(
            expressions = (
                expression.getType(), expression.getObject()
            ),
            names       = (
                "super_type", "super_object"
            ),
            emit        = emit,
            context     = context
        )

        Generator.getBuiltinSuperCode(
            to_name     = to_name,
            type_name   = type_name,
            object_name = object_name,
            emit        = emit,
            context     = context
        )
    elif expression.isExpressionYield():
        value_name = context.allocateTempName("yield")

        makeExpressionCode(
            to_name    = value_name,
            expression = expression.getExpression()
        )

        Generator.getYieldCode(
            to_name    = to_name,
            value_name = value_name,
            in_handler = expression.isExceptionPreserving(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionYieldFrom():
        value_name = context.allocateTempName("yield_from")

        makeExpressionCode(
            to_name    = value_name,
            expression = expression.getExpression()
        )

        Generator.getYieldFromCode(
            to_name    = to_name,
            value_name = value_name,
            in_handler = expression.isExceptionPreserving(),
            emit       = emit,
            context    = context
        )
    elif expression.isExpressionSideEffects():
        for side_effect in expression.getSideEffects():
            generateStatementOnlyCode(
                value   = side_effect,
                emit    = emit,
                context = context
            )

        makeExpressionCode(
            to_name    = to_name,
            expression = expression.getExpression()
        )
    elif expression.isExpressionBuiltinEval():
        generateEvalCode(
            to_name   = to_name,
            eval_node = expression,
            emit      = emit,
            context   = context
        )
    elif Utils.python_version < 300 and \
         expression.isExpressionBuiltinExecfile():
        generateExecfileCode(
            to_name       = to_name,
            execfile_node = expression,
            emit          = emit,
            context       = context
        )
    elif Utils.python_version >= 300 and \
         expression.isExpressionBuiltinExec():
        # exec builtin of Python3, as opposed to Python2 statement
        generateEvalCode(
            to_name   = to_name,
            eval_node = expression,
            emit      = emit,
            context   = context
        )
    elif expression.isExpressionBuiltinCompile():
        source_name = context.allocateTempName("compile_source")
        filename_name = context.allocateTempName("compile_filename")
        mode_name = context.allocateTempName("compile_mode")

        makeExpressionCode(
            to_name    = source_name,
            expression = expression.getSourceCode()
        )
        makeExpressionCode(
            to_name    = filename_name,
            expression = expression.getFilename()
        )
        makeExpressionCode(
            to_name    = mode_name,
            expression = expression.getMode()
        )

        if expression.getFlags() is not None:
            flags_name = context.allocateTempName("compile_flags")

            makeExpressionCode(
                to_name    = flags_name,
                expression = expression.getFlags(),
            )
        else:
            flags_name = "NULL"

        if expression.getDontInherit() is not None:
            dont_inherit_name = context.allocateTempName("compile_dont_inherit")

            makeExpressionCode(
                to_name    = dont_inherit_name,
                expression = expression.getDontInherit()
            )
        else:
            dont_inherit_name = "NULL"

        if expression.getOptimize() is not None:
            optimize_name = context.allocateTempName("compile_dont_inherit")

            makeExpressionCode(
                to_name    = optimize_name,
                expression = expression.getOptimize()
            )
        else:
            optimize_name = "NULL"

        Generator.getCompileCode(
            to_name           = to_name,
            source_name       = source_name,
            filename_name     = filename_name,
            mode_name         = mode_name,
            flags_name        = flags_name,
            dont_inherit_name = dont_inherit_name,
            optimize_name     = optimize_name,
            emit              = emit,
            context           = context
        )
    elif expression.isExpressionTryFinally():
        generateTryFinallyCode(
            to_name   = to_name,
            statement = expression,
            emit      = emit,
            context   = context
        )
    elif expression.isExpressionRaiseException():
        # Missed optimization opportunity, please report.
        if Options.isDebug():
            parent = expression.parent
            assert parent.isExpressionSideEffects() or \
                   parent.isExpressionConditional(), \
                   (expression, expression.parent)

        raise_type_name  = context.allocateTempName("raise_type")

        generateExpressionCode(
            to_name    = raise_type_name,
            expression = expression.getExceptionType(),
            emit       = emit,
            context    = context
        )

        raise_value_name  = context.allocateTempName("raise_value")

        generateExpressionCode(
            to_name    = raise_value_name,
            expression = expression.getExceptionValue(),
            emit       = emit,
            context    = context
        )

        emit("%s = NULL;" % to_name)

        Generator.getRaiseExceptionWithValueCode(
            raise_type_name  = raise_type_name,
            raise_value_name = raise_value_name,
            implicit         = True,
            emit             = emit,
            context          = context
        )
    else:
        assert False, expression

    context.setCurrentSourceCodeReference(old_source_ref)


def generateExpressionsCode(names, expressions, emit, context):
    assert len(names) == len(expressions)

    result = []
    for name, expression in zip(names, expressions):
        if expression is not None:
            to_name = context.allocateTempName(name)

            generateExpressionCode(
                to_name    = to_name,
                expression = expression,
                emit       = emit,
                context    = context
            )
        else:
            to_name = None

        result.append(to_name)

    return result


def generateExpressionCode(to_name, expression, emit, context,
                            allow_none = False):
    try:
        _generateExpressionCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context,
            allow_none = allow_none
        )
    except:
        Tracing.printError(
            "Problem with %r at %s" % (
                expression,
                ""
                  if expression is None else
                expression.getSourceReference().getAsString()
            )
        )
        raise


def generateAssignmentAttributeCode(statement, emit, context):
    lookup_source  = statement.getLookupSource()
    attribute_name = statement.getAttributeName()
    value          = statement.getAssignSource()

    value_name = context.allocateTempName("assattr_name")
    generateExpressionCode(
        to_name    = value_name,
        expression = value,
        emit       = emit,
        context    = context
    )

    target_name = context.allocateTempName("assattr_target")
    generateExpressionCode(
        to_name    = target_name,
        expression = lookup_source,
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        value.getSourceReference()
           if Options.isFullCompat() else
        statement.getSourceReference()
    )

    if attribute_name == "__dict__":
        Generator.getAttributeAssignmentDictSlotCode(
            target_name = target_name,
            value_name  = value_name,
            emit        = emit,
            context     = context
        )
    elif attribute_name == "__class__":
        Generator.getAttributeAssignmentClassSlotCode(
            target_name = target_name,
            value_name  = value_name,
            emit        = emit,
            context     = context
        )
    else:
        Generator.getAttributeAssignmentCode(
            target_name    = target_name,
            value_name     = value_name,
            attribute_name = Generator.getConstantCode(
                context  = context,
                constant = attribute_name
            ),
            emit           = emit,
            context        = context
        )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateAssignmentSubscriptCode(statement, emit, context):
    subscribed      = statement.getSubscribed()
    subscript       = statement.getSubscript()
    value           = statement.getAssignSource()

    integer_subscript = False
    if subscript.isExpressionConstantRef():
        constant = subscript.getConstant()

        if Constants.isIndexConstant(constant):
            constant_value = int(constant)

            if abs(constant_value) < 2**31:
                integer_subscript = True

    value_name = context.allocateTempName("ass_subvalue")

    generateExpressionCode(
        to_name    = value_name,
        expression = value,
        emit       = emit,
        context    = context
    )

    subscribed_name = context.allocateTempName("ass_subscribed")
    generateExpressionCode(
        to_name    = subscribed_name,
        expression = subscribed,
        emit       = emit,
        context    = context
    )


    subscript_name = context.allocateTempName("ass_subscript")

    generateExpressionCode(
        to_name    = subscript_name,
        expression = subscript,
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        value.getSourceReference()
           if Options.isFullCompat() else
        statement.getSourceReference()
    )

    if integer_subscript:
        Generator.getIntegerSubscriptAssignmentCode(
            subscribed_name = subscribed_name,
            subscript_name  = subscript_name,
            subscript_value = constant_value,
            value_name      = value_name,
            emit            = emit,
            context         = context
        )
    else:
        Generator.getSubscriptAssignmentCode(
            target_name    = subscribed_name,
            subscript_name = subscript_name,
            value_name     = value_name,
            emit           = emit,
            context        = context
        )
    context.setCurrentSourceCodeReference(old_source_ref)


def generateAssignmentSliceCode(statement, emit, context):
    assert Utils.python_version < 300

    lookup_source = statement.getLookupSource()
    lower         = statement.getLower()
    upper         = statement.getUpper()
    value         = statement.getAssignSource()

    value_name = context.allocateTempName("sliceass_value")

    generateExpressionCode(
        to_name    = value_name,
        expression = value,
        emit       = emit,
        context    = context
    )

    target_name = context.allocateTempName("sliceass_target")

    generateExpressionCode(
        to_name    = target_name,
        expression = lookup_source,
        emit       = emit,
        context    = context
    )


    if _decideSlicing(lower, upper):
        lower_name, upper_name = generateSliceRangeIdentifier(
            lower   = lower,
            upper   = upper,
            scope   = "sliceass",
            emit    = emit,
            context = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            value.getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        Generator.getSliceAssignmentIndexesCode(
            target_name = target_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            value_name  = value_name,
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    else:
        lower_name, upper_name = generateExpressionsCode(
            names       = (
                "sliceass_lower", "sliceass_upper"
            ),
            expressions = (
                lower,
                upper
            ),
            emit        = emit,
            context     = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            value.getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        Generator.getSliceAssignmentCode(
            target_name = target_name,
            upper_name  = upper_name,
            lower_name  = lower_name,
            value_name  = value_name,
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)


def generateVariableDelCode(statement, emit, context):
    old_source_ref = context.setCurrentSourceCodeReference(statement.getSourceReference())

    Generator.getVariableDelCode(
        variable = statement.getTargetVariableRef().getVariable(),
        tolerant = statement.isTolerant(),
        emit     = emit,
        context  = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateDelSubscriptCode(statement, emit, context):
    subscribed = statement.getSubscribed()
    subscript  = statement.getSubscript()

    target_name, subscript_name = generateExpressionsCode(
        expressions = (subscribed, subscript),
        names       = ("delsubscr_target", "delsubscr_subscript"),
        emit        = emit,
        context     = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        subscript.getSourceReference()
           if Options.isFullCompat() else
        statement.getSourceReference()
    )

    Generator.getSubscriptDelCode(
        target_name    = target_name,
        subscript_name = subscript_name,
        emit           = emit,
        context        = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateDelSliceCode(statement, emit, context):
    assert Utils.python_version < 300

    target  = statement.getLookupSource()
    lower   = statement.getLower()
    upper   = statement.getUpper()

    target_name = context.allocateTempName("slicedel_target")

    generateExpressionCode(
        to_name    = target_name,
        expression = target,
        emit       = emit,
        context    = context
    )

    if _decideSlicing(lower, upper):
        lower_name, upper_name = generateSliceRangeIdentifier(
            lower   = lower,
            upper   = upper,
            scope   = "slicedel",
            emit    = emit,
            context = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            (upper or lower or statement).getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        Generator.getSliceDelIndexesCode(
            target_name = target_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    else:
        lower_name, upper_name = generateExpressionsCode(
            names       = (
                "slicedel_lower", "slicedel_upper"
            ),
            expressions = (
                lower,
                upper
            ),
            emit        = emit,
            context     = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            (upper or lower or target).getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        Generator.getSliceDelCode(
            target_name = target_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)


def generateDelAttributeCode(statement, emit, context):
    target_name = context.allocateTempName("attrdel_target")

    generateExpressionCode(
        to_name    = target_name,
        expression = statement.getLookupSource(),
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getLookupSource().getSourceReference()
           if Options.isFullCompat() else
        statement.getSourceReference()
    )

    Generator.getAttributeDelCode(
        target_name    = target_name,
        attribute_name = Generator.getConstantCode(
            context  = context,
            constant = statement.getAttributeName()
        ),
        emit           = emit,
        context        = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)

def _generateEvalCode(to_name, node, emit, context):
    source_name = context.allocateTempName("eval_source")
    globals_name = context.allocateTempName("eval_globals")
    locals_name = context.allocateTempName("eval_locals")

    generateExpressionCode(
        to_name    = source_name,
        expression = node.getSourceCode(),
        emit       = emit,
        context    = context
    )

    generateExpressionCode(
        to_name    = globals_name,
        expression = node.getGlobals(),
        emit       = emit,
        context    = context
    )

    generateExpressionCode(
        to_name    = locals_name,
        expression = node.getLocals(),
        emit       = emit,
        context    = context
    )

    if node.isExpressionBuiltinEval() or \
         (Utils.python_version >= 300 and node.isExpressionBuiltinExec()):
        filename = "<string>"
    else:
        filename = "<execfile>"

    Generator.getEvalCode(
        to_name       = to_name,
        source_name   = source_name,
        globals_name  = globals_name,
        locals_name   = locals_name,
        filename_name = Generator.getConstantCode(
            constant = filename,
            context  = context
        ),
        mode_name     = Generator.getConstantCode(
            constant = "eval" if node.isExpressionBuiltinEval() else "exec",
            context  = context
        ),
        emit          = emit,
        context       = context
    )

def generateEvalCode(to_name, eval_node, emit, context):
    return _generateEvalCode(
        to_name = to_name,
        node    = eval_node,
        emit    = emit,
        context = context
    )

def generateExecfileCode(to_name, execfile_node, emit, context):
    return _generateEvalCode(
        to_name = to_name,
        node    = execfile_node,
        emit    = emit,
        context = context
    )

def generateExecCode(statement, emit, context):
    source_arg = statement.getSourceCode()
    globals_arg = statement.getGlobals()
    locals_arg = statement.getLocals()

    source_name = context.allocateTempName("eval_source")
    globals_name = context.allocateTempName("eval_globals")
    locals_name = context.allocateTempName("eval_locals")

    generateExpressionCode(
        to_name    = source_name,
        expression = source_arg,
        emit       = emit,
        context    = context
    )

    generateExpressionCode(
        to_name    = globals_name,
        expression = globals_arg,
        emit       = emit,
        context    = context
    )

    generateExpressionCode(
        to_name    = locals_name,
        expression = locals_arg,
        emit       = emit,
        context    = context
    )

    source_ref = statement.getSourceReference()

    # Filename with origin in improved mode.
    if Options.isFullCompat():
        filename_name = Generator.getConstantCode(
            constant = "<string>",
            context  = context
        )
    else:
        filename_name = Generator.getConstantCode(
            constant = "<string at %s>" % source_ref.getAsString(),
            context  = context
        )

    old_source_ref = context.setCurrentSourceCodeReference(
        locals_arg.getSourceReference()
          if Options.isFullCompat() else
        statement.getSourceReference()
    )

    Generator.getExecCode(
        source_name   = source_name,
        globals_name  = globals_name,
        locals_name   = locals_name,
        filename_name = filename_name,
        emit          = emit,
        context       = context,
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateLocalsDictSyncCode(statement, emit, context):
    locals_arg = statement.getLocals()
    locals_name = context.allocateTempName("eval_locals")

    generateExpressionCode(
        to_name    = locals_name,
        expression = locals_arg,
        emit       = emit,
        context    = context
    )

    provider = statement.getParentVariableProvider()

    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getSourceReference()
    )

    Generator.getLocalsDictSyncCode(
        locals_name = locals_name,
        provider    = provider,
        emit        = emit,
        context     = context,
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateTryNextExceptStopIterationCode(statement, emit, context):
    # This has many branches which mean this optimized code generation is not
    # applicable, we return each time. pylint: disable=R0911

    if statement.public_exc:
        return False

    handling = statement.getExceptionHandling()

    if handling is None:
        return False

    tried_statements = statement.getBlockTry().getStatements()

    if len(tried_statements) != 1:
        return False

    handling_statements = handling.getStatements()

    if len(handling_statements) != 1:
        return False

    tried_statement = tried_statements[0]

    if not tried_statement.isStatementAssignmentVariable():
        return False

    assign_source = tried_statement.getAssignSource()

    if not assign_source.isExpressionBuiltinNext1():
        return False

    handling_statement = handling_statements[0]

    if not handling_statement.isStatementConditional():
        return False

    yes_statements = handling_statement.getBranchYes().getStatements()
    no_statements = handling_statement.getBranchNo().getStatements()

    if len(yes_statements) != 1:
        return False

    if not yes_statements[0].isStatementBreakLoop():
        return False

    if len(no_statements) != 1:
        return False

    if not no_statements[0].isStatementReraiseException() or \
       not no_statements[0].isStatementReraiseException():
        return False

    tmp_name = context.allocateTempName("next_source")

    generateExpressionCode(
        expression = assign_source.getValue(),
        to_name    = tmp_name,
        emit       = emit,
        context    = context
    )

    tmp_name2 = context.allocateTempName("assign_source")

    old_source_ref = context.setCurrentSourceCodeReference(
        assign_source.getSourceReference()
          if Options.isFullCompat() else
        statement.getSourceReference()
    )

    Generator.getBuiltinLoopBreakNextCode(
        to_name = tmp_name2,
        value   = tmp_name,
        emit    = emit,
        context = context
    )

    Generator.getVariableAssignmentCode(
        tmp_name      = tmp_name2,
        variable      = tried_statement.getTargetVariableRef().getVariable(),
        emit          = emit,
        needs_release = None,
        context       = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)

    if context.needsCleanup(tmp_name2):
        context.removeCleanupTempName(tmp_name2)

    return True


def generateTryExceptCode(statement, emit, context):
    if generateTryNextExceptStopIterationCode(statement, emit, context):
        return

    tried_block = statement.getBlockTry()
    handling_block = statement.getExceptionHandling()

    # Optimization should not leave it present otherwise, something that cannot
    # raise, must already be reduced.
    assert tried_block.mayRaiseException(BaseException)

    old_ok = context.getExceptionNotOccurred()

    no_exception = context.allocateLabel("try_except_end")
    context.setExceptionNotOccurred(no_exception)

    old_escape = context.getExceptionEscape()
    context.setExceptionEscape(context.allocateLabel("try_except_handler"))

    emit("// Tried block of try/except")

    generateStatementSequenceCode(
        statement_sequence = tried_block,
        emit               = emit,
        context            = context,
    )

    Generator.getGotoCode(context.getExceptionNotOccurred(), emit)
    Generator.getLabelCode(context.getExceptionEscape(),emit)

    # Inside the exception handler, we need to error exit to the outside
    # handler.
    context.setExceptionEscape(old_escape)
    context.setExceptionNotOccurred(old_ok)

    old_published = context.isExceptionPublished()
    context.setExceptionPublished(statement.needsExceptionPublish())

    emit("// Exception handler of try/except")
    generateStatementSequenceCode(
        statement_sequence = handling_block,
        context            = context,
        emit               = emit,
        allow_none         = True
    )

    if handling_block is not None and handling_block.isStatementAborting():
        Generator.getExceptionUnpublishedReleaseCode(
            emit    = emit,
            context = context
        )

    # TODO: May have to do this for before return, break, and continue as well.
    if not statement.needsExceptionPublish():
        emit(
             """\
Py_DECREF( exception_type );
Py_XDECREF( exception_value );
Py_XDECREF( exception_tb );
"""
        )

    Generator.getLabelCode(no_exception,emit)

    context.setExceptionPublished(old_published)

_temp_whitelist = [()]

def generateTryFinallyCode(to_name, statement, emit, context):
    # The try/finally is very hard for C-ish code generation. We need to react
    # on break, continue, return, raise in the tried blocks with reraise. We
    # need to publish it to the handler (Python3) or save it for re-raise,
    # unless another exception or continue, break, return occurs. So this is
    # full of detail stuff, pylint: disable=R0914,R0912,R0915

    # First, this may be used as an expression, in which case to_name won't be
    # set, we ask the checks to ignore currently set values.
    if to_name is not None:
        _temp_whitelist.append(context.getCleanupTempnames())

    tried_block = statement.getBlockTry()
    final_block = statement.getBlockFinal()

    if to_name is not None:
        expression = statement.getExpression()
    else:
        expression = None

    # The tried statements might raise, for which we define an escape. As we
    # only want to have the final block one, we use this as the target for the
    # others, but make them set flags.
    old_escape = context.getExceptionEscape()
    tried_handler_escape = context.allocateLabel("try_finally_handler")
    context.setExceptionEscape(tried_handler_escape)

    # This is the handler start label, that is where we jump to.
    if statement.needsContinueHandling() or \
       statement.needsBreakHandling() or \
       statement.needsReturnHandling():
        handler_start_target = context.allocateLabel(
            "try_finally_handler_start"
        )
    else:
        handler_start_target = None

    # Set the indicator for "continue" and "break" first. Mostly for ease of
    # use, the C++ compiler can push it back as it sees fit. When an actual
    # continue or break occurs, they will set the indicators. We indicate
    # the name to use for that in the targets.
    if statement.needsContinueHandling():
        continue_name = context.allocateTempName("continue", "bool")

        emit("%s = false;" % continue_name)

        old_continue_target = context.getLoopContinueTarget()
        context.setLoopContinueTarget(
            handler_start_target,
            continue_name
        )

    # See above.
    if statement.needsBreakHandling():
        break_name = context.allocateTempName("break", "bool")

        emit("%s = false;" % break_name)

        old_break_target = context.getLoopBreakTarget()
        context.setLoopBreakTarget(
            handler_start_target,
            break_name
        )

    # For return, we need to catch that too.
    if statement.needsReturnHandling():
        old_return = context.getReturnTarget()
        context.setReturnTarget(handler_start_target)

    # Initialise expression, so even if it exits, the compiler will not see a
    # random value there. This shouldn't be necessary and hopefully the C++
    # compiler will find out. Since these are rare, it doesn't matter.
    if to_name is not None:
        # TODO: Silences the compiler for now. If we are honest, a real
        # Py_XDECREF would be needed at release time then.
        emit("%s = NULL;" % to_name)

    # Now the tried block can be generated.
    emit("// Tried code")
    generateStatementSequenceCode(
        statement_sequence = tried_block,
        emit               = emit,
        allow_none         = True,
        context            = context
    )

    # An eventual assignment of the tried expression if any is practically part
    # of the tried block, just last.
    if to_name is not None:
        generateExpressionCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context
        )

    # So this is when we completed the handler without exiting.
    if statement.needsReturnHandling() and Utils.python_version >= 330:
        emit(
            "tmp_return_value = NULL;"
        )

    if handler_start_target is not None:
        Generator.getLabelCode(handler_start_target,emit)

    # For the try/finally expression, we allow that the tried block may in fact
    # not raise, continue, or break at all, but it would merely be there to do
    # something before an expression. Kind of as a side effect. To address that
    # we need to check.
    tried_block_may_raise = tried_block is not None and \
                            tried_block.mayRaiseException(BaseException)
    # TODO: This should be true, but it isn't.
    # assert tried_block_may_raise or to_name is not None

    if not tried_block_may_raise:
        tried_block_may_raise = expression is not None and \
                                expression.mayRaiseException(BaseException)

    if tried_block_may_raise:
        emit("// Final block of try/finally")

        # The try/finally of Python3 might publish an exception to the handler,
        # which makes things more complex.
        if not statement.needsExceptionPublish():
            keeper_type, keeper_value, keeper_tb = \
                context.getExceptionKeeperVariables()

            emit(
                Generator.CodeTemplates.template_final_handler_start % {
                    "final_error_target" : context.getExceptionEscape(),
                    "keeper_type"        : keeper_type,
                    "keeper_value"       : keeper_value,
                    "keeper_tb"          : keeper_tb
                }
            )
        else:
            emit(
                Generator.CodeTemplates.template_final_handler_start_python3 % {
                    "final_error_target" : context.getExceptionEscape(),
                }
            )

    # Restore the handlers changed during the tried block. For the final block
    # we may set up others later.
    context.setExceptionEscape(old_escape)
    if statement.needsContinueHandling():
        context.setLoopContinueTarget(old_continue_target)
    if statement.needsBreakHandling():
        context.setLoopBreakTarget(old_break_target)
    if statement.needsReturnHandling():
        context.setReturnTarget(old_return)
    old_return_value_release = context.getReturnReleaseMode()
    context.setReturnReleaseMode(statement.needsReturnValueRelease())

    # If the final block might raise, we need to catch that, so we release a
    # preserved exception and don't leak it.
    final_block_may_raise = \
      final_block is not None and \
      final_block.mayRaiseException(BaseException) and \
      not statement.needsExceptionPublish()

    final_block_may_return = \
      final_block is not None and \
      final_block.mayReturn()

    final_block_may_break = \
      final_block is not None and \
      final_block.mayBreak()

    final_block_may_continue = \
      final_block is not None and \
      final_block.mayContinue()

    # That would be a SyntaxError
    assert not final_block_may_continue

    old_return = context.getReturnTarget()
    old_break_target = context.getLoopBreakTarget()
    old_continue_target = context.getLoopContinueTarget()

    if final_block is not None:
        if Utils.python_version < 300 and context.getFrameHandle() is not None:
            tried_lineno_name = context.allocateTempName("tried_lineno", "int")
            LineNumberCodes.getLineNumberCode(tried_lineno_name, emit, context)

        if final_block_may_raise:
            old_escape = context.getExceptionEscape()
            context.setExceptionEscape(
                context.allocateLabel("try_finally_handler_error")
            )

        if final_block_may_return:
            context.setReturnTarget(
                context.allocateLabel("try_finally_handler_return")
            )

        if final_block_may_break:
            context.setLoopBreakTarget(
                context.allocateLabel("try_finally_handler_break")
            )

        generateStatementSequenceCode(
            statement_sequence = final_block,
            emit               = emit,
            context            = context
        )

        if Utils.python_version < 300 and context.getFrameHandle() is not None:
            LineNumberCodes.getSetLineNumberCodeRaw(
                to_name = tried_lineno_name,
                emit    = emit,
                context = context
            )
    else:
        # Final block is only optional for try/finally expressions. For
        # statements, they should be optimized way.
        assert to_name is not None

    context.setReturnReleaseMode(old_return_value_release)

    emit("// Re-reraise as necessary after finally was executed.")

    if tried_block_may_raise and not statement.needsExceptionPublish():
        emit(
            Generator.CodeTemplates.template_final_handler_reraise % {
                "exception_exit" : old_escape,
                "keeper_type"    : keeper_type,
                "keeper_value"   : keeper_value,
                "keeper_tb"      : keeper_tb
            }
        )

    if Utils.python_version >= 330:
        return_template = Generator.CodeTemplates.\
          template_final_handler_return_reraise
    else:
        provider = statement.getParentVariableProvider()

        if not provider.isExpressionFunctionBody() or \
           not provider.isGenerator():
            return_template = Generator.CodeTemplates.\
              template_final_handler_return_reraise
        else:
            return_template = Generator.CodeTemplates.\
              template_final_handler_generator_return_reraise

    if statement.needsReturnHandling():
        emit(
            return_template % {
                "parent_return_target" : old_return
            }
        )

    if statement.needsContinueHandling():
        emit(
            """\
// Continue if entered via continue.
if ( %(continue_name)s )
{
""" % {
                "continue_name" : continue_name
            }
        )

        if type(old_continue_target) is tuple:
            emit("%s = true;" % old_continue_target[1])
            Generator.getGotoCode(old_continue_target[0], emit)
        else:
            Generator.getGotoCode(old_continue_target, emit)

        emit("}")
    if statement.needsBreakHandling():
        emit(
            """\
// Break if entered via break.
if ( %(break_name)s )
{
""" % {
                "break_name" : break_name
            }
        )

        if type(old_break_target) is tuple:
            emit("%s = true;" % old_break_target[1])
            Generator.getGotoCode(old_break_target[0], emit)
        else:
            Generator.getGotoCode(old_break_target, emit)

        emit("}")

    final_end_target = context.allocateLabel("finally_end")
    Generator.getGotoCode(final_end_target, emit)

    if final_block_may_raise:
        Generator.getLabelCode(context.getExceptionEscape(),emit)

        # TODO: Avoid the labels in this case
        if tried_block_may_raise:
            if Utils.python_version < 300:
                emit(
                    """\
Py_XDECREF( %(keeper_type)s );%(keeper_type)s = NULL;
Py_XDECREF( %(keeper_value)s );%(keeper_value)s = NULL;
Py_XDECREF( %(keeper_tb)s );%(keeper_tb)s = NULL;""" % {
                        "keeper_type"  : keeper_type,
                        "keeper_value" : keeper_value,
                        "keeper_tb"    : keeper_tb
                    }
                )
            else:
                emit("""\
if ( %(keeper_type)s )
{
    NORMALIZE_EXCEPTION( &%(keeper_type)s, &%(keeper_value)s, &%(keeper_tb)s );
    if( exception_value != %(keeper_value)s )
    {
        PyException_SetContext( %(keeper_value)s, exception_value );
    }
    else
    {
        Py_DECREF( exception_value );
    }
    Py_DECREF( exception_type );
    exception_type = %(keeper_type)s;
    exception_value = %(keeper_value)s;
    Py_XDECREF( exception_tb );
    exception_tb = %(keeper_tb)s;
}
""" % {
                        "keeper_type"  : keeper_type,
                        "keeper_value" : keeper_value,
                        "keeper_tb"    : keeper_tb
                    })


        context.setExceptionEscape(old_escape)
        Generator.getGotoCode(context.getExceptionEscape(), emit)

    if final_block_may_return:
        Generator.getLabelCode(context.getReturnTarget(),emit)

        # TODO: Avoid the labels in this case
        if tried_block_may_raise and not statement.needsExceptionPublish():
            emit(
                """\
Py_XDECREF( %(keeper_type)s );%(keeper_type)s = NULL;
Py_XDECREF( %(keeper_value)s );%(keeper_value)s = NULL;
Py_XDECREF( %(keeper_tb)s );%(keeper_tb)s = NULL;""" % {
                "keeper_type"  : keeper_type,
                "keeper_value" : keeper_value,
                "keeper_tb"    : keeper_tb
            }
        )

        context.setReturnTarget(old_return)
        Generator.getGotoCode(context.getReturnTarget(), emit)

    if final_block_may_break:
        Generator.getLabelCode(context.getLoopBreakTarget(),emit)

        # TODO: Avoid the labels in this case
        if tried_block_may_raise and not statement.needsExceptionPublish():
            emit(
            """\
Py_XDECREF( %(keeper_type)s );%(keeper_type)s = NULL;
Py_XDECREF( %(keeper_value)s );%(keeper_value)s = NULL;
Py_XDECREF( %(keeper_tb)s );%(keeper_tb)s = NULL;""" % {
                "keeper_type"  : keeper_type,
                "keeper_value" : keeper_value,
                "keeper_tb"    : keeper_tb
            }
        )

        context.setLoopBreakTarget(old_break_target)
        Generator.getGotoCode(context.getLoopBreakTarget(),emit)

    Generator.getLabelCode(final_end_target,emit)

    # Restore whitelist to previous state.
    if to_name is not None:
        _temp_whitelist.pop()


def generateRaiseCode(statement, emit, context):
    exception_type  = statement.getExceptionType()
    exception_value = statement.getExceptionValue()
    exception_tb    = statement.getExceptionTrace()
    exception_cause = statement.getExceptionCause()

    context.markAsNeedsExceptionVariables()

    # Exception cause is only possible with simple raise form.
    if exception_cause is not None:
        assert exception_type is not None
        assert exception_value is None
        assert exception_tb is None

        raise_type_name  = context.allocateTempName("raise_type")

        generateExpressionCode(
            to_name    = raise_type_name,
            expression = exception_type,
            emit       = emit,
            context    = context
        )

        raise_cause_name  = context.allocateTempName("raise_type")

        generateExpressionCode(
            to_name    = raise_cause_name,
            expression = exception_cause,
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(exception_cause.getSourceReference())

        Generator.getRaiseExceptionWithCauseCode(
            raise_type_name  = raise_type_name,
            raise_cause_name = raise_cause_name,
            emit             = emit,
            context          = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    elif exception_type is None:
        assert exception_cause is None
        assert exception_value is None
        assert exception_tb is None

        Generator.getReRaiseExceptionCode(
            emit    = emit,
            context = context
        )
    elif exception_value is None and exception_tb is None:
        raise_type_name  = context.allocateTempName("raise_type")

        generateExpressionCode(
            to_name    = raise_type_name,
            expression = exception_type,
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(exception_type.getSourceReference())

        Generator.getRaiseExceptionWithTypeCode(
            raise_type_name = raise_type_name,
            emit            = emit,
            context         = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    elif exception_tb is None:
        raise_type_name  = context.allocateTempName("raise_type")

        generateExpressionCode(
            to_name    = raise_type_name,
            expression = exception_type,
            emit       = emit,
            context    = context
        )

        raise_value_name  = context.allocateTempName("raise_value")

        generateExpressionCode(
            to_name    = raise_value_name,
            expression = exception_value,
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(exception_value.getSourceReference())

        Generator.getRaiseExceptionWithValueCode(
            raise_type_name  = raise_type_name,
            raise_value_name = raise_value_name,
            implicit         = statement.isImplicit(),
            emit             = emit,
            context          = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    else:
        raise_type_name  = context.allocateTempName("raise_type")

        generateExpressionCode(
            to_name    = raise_type_name,
            expression = exception_type,
            emit       = emit,
            context    = context
        )

        raise_value_name  = context.allocateTempName("raise_value")

        generateExpressionCode(
            to_name    = raise_value_name,
            expression = exception_value,
            emit       = emit,
            context    = context
        )

        raise_tb_name = context.allocateTempName("raise_tb")

        generateExpressionCode(
            to_name    = raise_tb_name,
            expression = exception_tb,
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(exception_tb.getSourceReference())

        Generator.getRaiseExceptionWithTracebackCode(
            raise_type_name  = raise_type_name,
            raise_value_name = raise_value_name,
            raise_tb_name    = raise_tb_name,
            emit             = emit,
            context          = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)


def generateUnpackCheckCode(statement, emit, context):
    iterator_name  = context.allocateTempName("iterator_name")

    generateExpressionCode(
        to_name    = iterator_name,
        expression = statement.getIterator(),
        emit       = emit,
        context    = context
    )

    Generator.getUnpackCheckCode(
        iterator_name = iterator_name,
        count         = statement.getCount(),
        emit          = emit,
        context       = context,
    )


def generateImportModuleCode(to_name, expression, emit, context):
    provider = expression.getParentVariableProvider()

    globals_name = context.allocateTempName("import_globals")

    Generator.getLoadGlobalsCode(
        to_name = globals_name,
        emit    = emit,
        context = context
    )

    if provider.isPythonModule():
        locals_name = globals_name
    else:
        locals_name = context.allocateTempName("import_locals")

        Generator.getLoadLocalsCode(
            to_name  = locals_name,
            provider = expression.getParentVariableProvider(),
            mode     = "updated",
            emit     = emit,
            context  = context
        )

    old_source_ref = context.setCurrentSourceCodeReference(expression.getSourceReference())

    Generator.getBuiltinImportCode(
        to_name          = to_name,
        module_name      = Generator.getConstantCode(
            constant = expression.getModuleName(),
            context  = context
        ),
        globals_name     = globals_name,
        locals_name      = locals_name,
        import_list_name = Generator.getConstantCode(
            constant = expression.getImportList(),
            context  = context
        ),
        level_name       = Generator.getConstantCode(
            constant = expression.getLevel(),
            context  = context
        ),
        emit             = emit,
        context          = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateBuiltinImportCode(to_name, expression, emit, context):
    # We know that 5 expressions are created, pylint: disable=W0632
    module_name, globals_name, locals_name, import_list_name, level_name = \
      generateExpressionsCode(
        expressions = (
            expression.getImportName(),
            expression.getGlobals(),
            expression.getLocals(),
            expression.getFromList(),
            expression.getLevel()
        ),
        names       = (
            "import_modulename",
            "import_globals",
            "import_locals",
            "import_fromlist",
            "import_level"
        ),
        emit        = emit,
        context     = context
    )

    if expression.getGlobals() is None:
        globals_name = context.allocateTempName("import_globals")

        Generator.getLoadGlobalsCode(
            to_name = globals_name,
            emit    = emit,
            context = context
        )

    if expression.getLocals() is None:
        provider = expression.getParentVariableProvider()

        if provider.isPythonModule():
            locals_name = globals_name
        else:
            locals_name = context.allocateTempName("import_locals")

            Generator.getLoadLocalsCode(
                to_name  = locals_name,
                provider = provider,
                mode     = provider.getLocalsMode(),
                emit     = emit,
                context  = context
            )


    Generator.getBuiltinImportCode(
        to_name          = to_name,
        module_name      = module_name,
        globals_name     = globals_name,
        locals_name      = locals_name,
        import_list_name = import_list_name,
        level_name       = level_name,
        emit             = emit,
        context          = context
    )


def generateImportStarCode(statement, emit, context):
    module_name = context.allocateTempName("star_imported")

    generateImportModuleCode(
        to_name    = module_name,
        expression = statement.getModule(),
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(statement.getSourceReference())

    Generator.getImportFromStarCode(
        module_name = module_name,
        emit        = emit,
        context     = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateBranchCode(statement, emit, context):
    true_target = context.allocateLabel("branch_yes")
    false_target = context.allocateLabel("branch_no")
    end_target = context.allocateLabel("branch_end")

    old_true_target = context.getTrueBranchTarget()
    old_false_target = context.getFalseBranchTarget()

    context.setTrueBranchTarget(true_target)
    context.setFalseBranchTarget(false_target)

    generateConditionCode(
        condition = statement.getCondition(),
        emit      = emit,
        context   = context
    )

    context.setTrueBranchTarget(old_true_target)
    context.setFalseBranchTarget(old_false_target)

    Generator.getLabelCode(true_target, emit)

    generateStatementSequenceCode(
        statement_sequence = statement.getBranchYes(),
        emit               = emit,
        context            = context
    )

    if statement.getBranchNo() is not None:
        Generator.getGotoCode(end_target, emit)
        Generator.getLabelCode(false_target, emit)

        generateStatementSequenceCode(
            statement_sequence = statement.getBranchNo(),
            emit               = emit,
            context            = context
        )

        Generator.getLabelCode(end_target, emit)
    else:
        Generator.getLabelCode(false_target, emit)


def generateLoopCode(statement, emit, context):
    loop_start_label = context.allocateLabel("loop_start")
    if not statement.isStatementAborting():
        loop_end_label = context.allocateLabel("loop_end")
    else:
        loop_end_label = None

    Generator.getLabelCode(loop_start_label, emit)

    old_loop_break = context.getLoopBreakTarget()
    old_loop_continue = context.getLoopContinueTarget()

    context.setLoopBreakTarget(loop_end_label)
    context.setLoopContinueTarget(loop_start_label)

    generateStatementSequenceCode(
        statement_sequence = statement.getLoopBody(),
        allow_none         = True,
        emit               = emit,
        context            = context
    )

    context.setLoopBreakTarget(old_loop_break)
    context.setLoopContinueTarget(old_loop_continue)

    # Note: We are using the wrong line here, but it's an exception, it's unclear what line it would be anyway.
    old_source_ref = context.setCurrentSourceCodeReference(statement.getSourceReference())

    Generator.getErrorExitBoolCode(
        condition = "CONSIDER_THREADING() == false",
        emit      = emit,
        context   = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)

    Generator.getGotoCode(loop_start_label, emit)

    if loop_end_label is not None:
        Generator.getLabelCode(loop_end_label, emit)


def generateReturnCode(statement, emit, context):
    return_value_name = context.getReturnValueName()

    if context.getReturnReleaseMode():
        emit("Py_DECREF( %s );" % return_value_name)

    generateExpressionCode(
        to_name    = return_value_name,
        expression = statement.getExpression(),
        emit       = emit,
        context    = context
    )

    if context.needsCleanup(return_value_name):
        context.removeCleanupTempName(return_value_name)
    else:
        emit(
            "Py_INCREF( %s );" % return_value_name
        )

    Generator.getGotoCode(context.getReturnTarget(), emit)


def generateGeneratorReturnCode(statement, emit, context):
    if Utils.python_version >= 330:
        return_value_name = context.getGeneratorReturnValueName()

        expression = statement.getExpression()

        if context.getReturnReleaseMode():
            emit("Py_DECREF( %s );" % return_value_name)

        generateExpressionCode(
            to_name    = return_value_name,
            expression = expression,
            emit       = emit,
            context    = context
        )

        if context.needsCleanup(return_value_name):
            context.removeCleanupTempName(return_value_name)
        else:
            emit(
                "Py_INCREF( %s );" % return_value_name
            )
    elif statement.getParentVariableProvider().needsGeneratorReturnHandling():
        return_value_name = context.getGeneratorReturnValueName()

        generator_return_name = context.allocateTempName(
            "generator_return",
            "bool",
            unique = True
        )

        emit("%s = true;" % generator_return_name)

    Generator.getGotoCode(context.getReturnTarget(), emit)


def generateAssignmentVariableCode(statement, emit, context):
    variable_ref  = statement.getTargetVariableRef()
    value         = statement.getAssignSource()

    tmp_name = context.allocateTempName("assign_source")

    generateExpressionCode(
        expression = value,
        to_name    = tmp_name,
        emit       = emit,
        context    = context
    )

    Generator.getVariableAssignmentCode(
        tmp_name      = tmp_name,
        variable      = variable_ref.getVariable(),
        needs_release = statement.needsReleaseValue(),
        emit          = emit,
        context       = context
    )

    # Ownership of that reference should be transfered.
    assert not context.needsCleanup(tmp_name)


def generateStatementOnlyCode(value, emit, context):
    tmp_name = context.allocateTempName(
        base_name = "unused",
        type_code = "NUITKA_MAY_BE_UNUSED PyObject *",
        unique    = True
    )

    generateExpressionCode(
        expression = value,
        to_name    = tmp_name,
        emit       = emit,
        context    = context
    )

    Generator.getReleaseCode(
        release_name = tmp_name,
        emit         = emit,
        context      = context
    )


def generatePrintValueCode(statement, emit, context):
    destination = statement.getDestination()
    value       = statement.getValue()

    if destination is not None:
        tmp_name_dest = context.allocateTempName("print_dest", unique = True)

        generateExpressionCode(
            expression = destination,
            to_name    = tmp_name_dest,
            emit       = emit,
            context    = context
        )
    else:
        tmp_name_dest = None

    tmp_name_printed = context.allocateTempName("print_value", unique = True)

    generateExpressionCode(
        expression = value,
        to_name    = tmp_name_printed,
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(statement.getSourceReference())

    Generator.getPrintValueCode(
        dest_name  = tmp_name_dest,
        value_name = tmp_name_printed,
        emit       = emit,
        context    = context
    )
    context.setCurrentSourceCodeReference(old_source_ref)


def generatePrintNewlineCode(statement, emit, context):
    destination = statement.getDestination()

    if destination is not None:
        tmp_name_dest = context.allocateTempName("print_dest", unique = True)

        generateExpressionCode(
            expression = destination,
            to_name    = tmp_name_dest,
            emit       = emit,
            context    = context
        )
    else:
        tmp_name_dest = None

    old_source_ref = context.setCurrentSourceCodeReference(statement.getSourceReference())
    Generator.getPrintNewlineCode(
        dest_name = tmp_name_dest,
        emit      = emit,
        context   = context
    )
    context.setCurrentSourceCodeReference(old_source_ref)


def _generateStatementCode(statement, emit, context):
    # This is a dispatching function with a branch per statement node type.
    # pylint: disable=R0912,R0915
    if not statement.isStatement():
        statement.dump()
        assert False

    if statement.isStatementAssignmentVariable():
        generateAssignmentVariableCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementAssignmentAttribute():
        generateAssignmentAttributeCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementAssignmentSubscript():
        generateAssignmentSubscriptCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementAssignmentSlice():
        generateAssignmentSliceCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementDelVariable():
        generateVariableDelCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementDelSubscript():
        generateDelSubscriptCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementDelSlice():
        generateDelSliceCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementDelAttribute():
        generateDelAttributeCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementExpressionOnly():
        generateStatementOnlyCode(
            value   = statement.getExpression(),
            emit    = emit,
            context = context
        )
    elif statement.isStatementReturn():
        generateReturnCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementGeneratorReturn():
        generateGeneratorReturnCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementConditional():
        generateBranchCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementTryExcept():
        generateTryExceptCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementTryFinally():
        generateTryFinallyCode(
            to_name   = None, # Not a try/finally expression.
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementPrintValue():
        generatePrintValueCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementPrintNewline():
        generatePrintNewlineCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementImportStar():
        generateImportStarCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementLoop():
        generateLoopCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementBreakLoop():
        Generator.getLoopBreakCode(
            emit    = emit,
            context = context
        )
    elif statement.isStatementContinueLoop():
        Generator.getLoopContinueCode(
            emit    = emit,
            context = context
        )
    elif statement.isStatementRaiseException():
        generateRaiseCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementSpecialUnpackCheck():
        generateUnpackCheckCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementExec():
        generateExecCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementLocalsDictSync():
        generateLocalsDictSyncCode(
            statement = statement,
            emit      = emit,
            context   = context
        )
    elif statement.isStatementDictOperationRemove():
        dict_name = context.allocateTempName("remove_dict", unique = True)
        key_name = context.allocateTempName("remove_key", unique = True)

        generateExpressionCode(
            to_name    = dict_name,
            expression = statement.getDict(),
            emit       = emit,
            context    = context
        )
        generateExpressionCode(
            to_name    = key_name,
            expression = statement.getKey(),
            emit       = emit,
            context    = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            statement.getKey().getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        Generator.getDictOperationRemoveCode(
            dict_name = dict_name,
            key_name  = key_name,
            emit      = emit,
            context   = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(old_source_ref)
    elif statement.isStatementSetLocals():
        new_locals_name = context.allocateTempName("set_locals", unique = True)

        generateExpressionCode(
            to_name    = new_locals_name,
            expression = statement.getNewLocals(),
            emit       = emit,
            context    = context
        )

        Generator.getSetLocalsCode(
            new_locals_name = new_locals_name,
            emit            = emit,
            context         = context
        )
    elif statement.isStatementGeneratorEntry():
        emit(
            Generator.CodeTemplates.template_generator_initial_throw % {
                "frame_exception_exit" : context.getExceptionEscape()
            }
        )
    elif statement.isStatementPreserveFrameException():
        Generator.getFramePreserveExceptionCode(
            emit    = emit,
            context = context
        )
    elif statement.isStatementRestoreFrameException():
        Generator.getFrameRestoreExceptionCode(
            emit    = emit,
            context = context
        )
    elif statement.isStatementReraiseFrameException():
        Generator.getFrameReraiseExceptionCode(
            emit    = emit,
            context = context
        )
    elif statement.isStatementPublishException():
        context.markAsNeedsExceptionVariables()

        emit(
            Generator.CodeTemplates.template_publish_exception_to_handler % {
                "tb_making"        : Generator.getTracebackMakingIdentifier(
                    context = context
                ),
                "frame_identifier" : context.getFrameHandle()
            }
        )

        emit(
            "NORMALIZE_EXCEPTION( &exception_type, &exception_value, &exception_tb );"
        )
        if Utils.python_version >= 300:
            emit(
                """PyException_SetTraceback( exception_value, (PyObject *)exception_tb );"""
            )

        emit(
            "PUBLISH_EXCEPTION( &exception_type, &exception_value, &exception_tb );"
        )

    else:
        assert False, statement


def generateStatementCode(statement, emit, context):
    try:
        _generateStatementCode(statement, emit, context)

        try_finally_candidate = statement.parent.getParent()

        if try_finally_candidate is not None and \
           not try_finally_candidate.isExpression():
            # Complain if any temporary was not dealt with yet.
            assert not context.getCleanupTempnames() or \
                  context.getCleanupTempnames() == _temp_whitelist[-1], \
              context.getCleanupTempnames()
    except Exception:
        Tracing.printError(
            "Problem with %r at %s" % (
                statement,
                statement.getSourceReference().getAsString()
            )
        )
        raise


def _generateStatementSequenceCode(statement_sequence, emit, context,
                                   allow_none = False):

    if statement_sequence is None and allow_none:
        return

    for statement in statement_sequence.getStatements():
        source_ref = statement.getSourceReference()

        if Options.shallTraceExecution():
            statement_repr = repr(statement)
            source_repr = source_ref.getAsString()

            if Utils.python_version >= 300:
                statement_repr = statement_repr.encode("utf8")
                source_repr = source_repr.encode("utf8")

            emit(
                Generator.getStatementTrace(
                    source_repr,
                    statement_repr
                )
            )

        if statement.isStatementsSequence():
            generateStatementSequenceCode(
                statement_sequence = statement,
                emit               = emit,
                context            = context
            )
        else:
            generateStatementCode(
                statement = statement,
                emit      = emit,
                context   = context
            )


def generateStatementsFrameCode(statement_sequence, emit, context):
    # This is a wrapper that provides also handling of frames, which got a
    # lot of variants and details, therefore lots of branches.
    # pylint: disable=R0912

    provider = statement_sequence.getParentVariableProvider()
    guard_mode = statement_sequence.getGuardMode()

    parent_exception_exit = context.getExceptionEscape()

    if guard_mode != "pass_through":
        if provider.isExpressionFunctionBody():
            context.setFrameHandle("frame_function")
        else:
            context.setFrameHandle("frame_module")

        context.setExceptionEscape(
            context.allocateLabel("frame_exception_exit")
        )
    else:
        context.setFrameHandle("PyThreadState_GET()->frame")

    needs_preserve = statement_sequence.needsFrameExceptionPreserving()

    if statement_sequence.mayReturn() and guard_mode != "pass_through":
        parent_return_exit = context.getReturnTarget()

        context.setReturnTarget(
            context.allocateLabel("frame_return_exit")
        )
    else:
        parent_return_exit = None

    # Now generate the statements code into a local buffer, to we can wrap
    # the frame stuff around it.
    local_emit = Emission.SourceCodeCollector()

    _generateStatementSequenceCode(
        statement_sequence = statement_sequence,
        emit               = local_emit,
        context            = context
    )

    if statement_sequence.mayRaiseException(BaseException) or \
       guard_mode == "generator":
        frame_exception_exit = context.getExceptionEscape()
    else:
        frame_exception_exit = None

    if parent_return_exit is not None:
        frame_return_exit = context.getReturnTarget()
    else:
        frame_return_exit = None

    if guard_mode == "generator":
        assert provider.isExpressionFunctionBody() and \
               provider.isGenerator()

        # TODO: This case should care about "needs_preserve", as for
        # Python3 it is actually not a stub of empty code.

        codes = Generator.getFrameGuardLightCode(
            frame_identifier      = context.getFrameHandle(),
            code_identifier       = statement_sequence.getCodeObjectHandle(
                context = context
            ),
            codes                 = local_emit.codes,
            parent_exception_exit = parent_exception_exit,
            frame_exception_exit  = frame_exception_exit,
            parent_return_exit    = parent_return_exit,
            frame_return_exit     = frame_return_exit,
            provider              = provider,
            context               = context
        ).split("\n")
    elif guard_mode == "pass_through":
        assert provider.isExpressionFunctionBody()

        # This case does not care about "needs_preserve", as for that kind
        # of frame, it is an empty code stub anyway.
        codes = "\n".join(local_emit.codes),
    elif guard_mode == "full":
        assert provider.isExpressionFunctionBody()

        codes = Generator.getFrameGuardHeavyCode(
            frame_identifier      = context.getFrameHandle(),
            code_identifier       = statement_sequence.getCodeObjectHandle(
                context
            ),
            parent_exception_exit = parent_exception_exit,
            parent_return_exit    = parent_return_exit,
            frame_exception_exit  = frame_exception_exit,
            frame_return_exit     = frame_return_exit,
            codes                 = local_emit.codes,
            needs_preserve        = needs_preserve,
            provider              = provider,
            context               = context
        ).split("\n")
    elif guard_mode == "once":
        codes = Generator.getFrameGuardOnceCode(
            frame_identifier      = context.getFrameHandle(),
            code_identifier       = statement_sequence.getCodeObjectHandle(
                context = context
            ),
            parent_exception_exit = parent_exception_exit,
            parent_return_exit    = parent_return_exit,
            frame_exception_exit  = frame_exception_exit,
            frame_return_exit     = frame_return_exit,
            codes                 = local_emit.codes,
            needs_preserve        = needs_preserve,
            provider              = provider,
            context               = context
        ).split("\n")
    else:
        assert False, guard_mode

    context.setExceptionEscape(parent_exception_exit)

    if frame_return_exit is not None:
        context.setReturnTarget(parent_return_exit)

    for line in codes:
        emit(line)


def generateStatementSequenceCode(statement_sequence, emit, context,
                                  allow_none = False):

    if allow_none and statement_sequence is None:
        return None

    assert statement_sequence.isStatementsSequence(), statement_sequence

    statement_context = Contexts.PythonStatementCContext(context)

    if statement_sequence.isStatementsFrame():
        generateStatementsFrameCode(
            statement_sequence = statement_sequence,
            emit               = emit,
            context            = statement_context
        )
    else:
        _generateStatementSequenceCode(
            statement_sequence = statement_sequence,
            emit               = emit,
            context            = statement_context
        )

    # Complain if any temporary was not dealt with yet.
    assert not statement_context.getCleanupTempnames(), \
      statement_context.getCleanupTempnames()


def prepareModuleCode(global_context, module, module_name, other_modules):
    # As this not only creates all modules, but also functions, it deals
    # with too many details, pylint: disable=R0914

    assert module.isPythonModule(), module

    context = Contexts.PythonModuleContext(
        module         = module,
        module_name    = module_name,
        code_name      = module.getCodeName(),
        filename       = module.getFilename(),
        global_context = global_context,
        is_empty       = module.getBody() is None
    )

    context.setExceptionEscape("module_exception_exit")

    statement_sequence = module.getBody()

    codes = []

    generateStatementSequenceCode(
        statement_sequence = statement_sequence,
        emit               = codes.append,
        allow_none         = True,
        context            = context,
    )

    function_decl_codes = []
    function_body_codes = []

    for function_body in module.getUsedFunctions():
        function_code = generateFunctionBodyCode(
            function_body = function_body,
            context       = context
        )

        assert type(function_code) is str

        function_body_codes.append(function_code)

        if function_body.needsDirectCall():
            function_decl = Generator.getFunctionDirectDecl(
                function_identifier = function_body.getCodeName(),
                closure_variables   = function_body.getClosureVariables(),
                parameter_variables = function_body.getParameters().getAllVariables(),
                file_scope          = Generator.getExportScopeCode(
                    cross_module = function_body.isCrossModuleUsed()
                )
            )

            function_decl_codes.append(function_decl)

    for function_body in module.getCrossUsedFunctions():
        assert function_body.isCrossModuleUsed()

        function_decl = Generator.getFunctionDirectDecl(
            function_identifier = function_body.getCodeName(),
            closure_variables   = function_body.getClosureVariables(),
            parameter_variables = function_body.getParameters().getAllVariables(),
            file_scope          = Generator.getExportScopeCode(
                cross_module = function_body.isCrossModuleUsed()
            )
        )

        function_decl_codes.append(function_decl)

    for _identifier, code in sorted(iterItems(context.getHelperCodes())):
        function_body_codes.append(code)

    for _identifier, code in sorted(iterItems(context.getDeclarations())):
        function_decl_codes.append(code)

    function_body_codes = "\n\n".join(function_body_codes)
    function_decl_codes = "\n\n".join(function_decl_codes)

    metapath_loader_inittab = []
    metapath_module_decls = []

    for other_module in other_modules:
        metapath_loader_inittab.append(
            Generator.getModuleMetapathLoaderEntryCode(
                module_name       = other_module.getFullName(),
                module_identifier = other_module.getCodeName(),
                is_shlib          = other_module.isPythonShlibModule(),
                is_package        = other_module.isPythonPackage()
            )
        )

        if not other_module.isPythonShlibModule():
            metapath_module_decls.append(
                "MOD_INIT_DECL( %s );" % other_module.getCodeName()
            )

    template_values = Generator.prepareModuleCode(
        module_name             = module_name,
        module_identifier       = module.getCodeName(),
        codes                   = codes,
        metapath_loader_inittab = metapath_loader_inittab,
        metapath_module_decls   = metapath_module_decls,
        function_decl_codes     = function_decl_codes,
        function_body_codes     = function_body_codes,
        temp_variables          = module.getTempVariables(),
        is_main_module          = module.isMainModule(),
        is_internal_module      = module.isInternalModule(),
        context                 = context
    )

    if Utils.python_version >= 330:
        context.getConstantCode("__loader__")

    return template_values, context

def generateModuleCode(module_context, template_values):
    return Generator.getModuleCode(
        module_context  = module_context,
        template_values = template_values
    )


def generateMainCode(main_module, codes, context):
    return Generator.getMainCode(
        main_module = main_module,
        context     = context,
        codes       = codes
    )


def generateConstantsDefinitionCode(context):
    return Generator.getConstantsDefinitionCode(
        context = context
    )


def generateHelpersCode():
    header_code = Generator.getCallsDecls()

    body_code = Generator.getCallsCode()

    return header_code, body_code


def makeGlobalContext():
    return Contexts.PythonGlobalContext()


# TODO: Find a proper home for this code
def generateBuiltinIdCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name  = to_name,
        capi     = "PyLong_FromVoidPtr",
        arg_desc = (
            ("id_arg", expression.getValue()),
        ),
        emit     = emit,
        context  = context
    )


Helpers.setExpressionDispatchDict(
    {
        "VARIABLE_REF"      : generateVariableReferenceCode,
        "TEMP_VARIABLE_REF" : generateVariableReferenceCode,
        "CONSTANT_REF"      : generateConstantReferenceCode,
        "ATTRIBUTE_LOOKUP"  : generateAttributeLookupCode,
        "SUBSCRIPT_LOOKUP"  : generateSubscriptLookupCode,
        "BUILTIN_SLICE"     : generateBuiltinSliceCode,
        "BUILTIN_ID"        : generateBuiltinIdCode
    }
)
