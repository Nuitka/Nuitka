#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Generator for C++ and Python C/API.

This is the actual C++ code generator. It has methods and should be the only place to know
what C++ is like. Ideally it would be possible to replace the target language by changing
this one and the templates, and otherwise nothing else.

"""


from .Identifiers import (
    Identifier,
    ModuleVariableIdentifier,
    HelperCallIdentifier,
    ThrowingIdentifier,
    CallIdentifier,
    NullIdentifier,
    EmptyDictIdentifier,
    getCodeTemporaryRefs,
    getCodeExportRefs,

)

from .Indentation import indented

from .Pickling import getStreamedConstant

from .OrderedEvaluation import getEvalOrderedCode

from .ConstantCodes import getConstantHandle, getConstantCode

# These are here to be imported from here
# pylint: disable=W0611
from .VariableCodes import getVariableHandle, getVariableCode, getLocalVariableInitCode
# pylint: enable=W0611

from .TupleCodes import getTupleCreationCode
from .ListCodes import getListCreationCode # imported from here pylint: disable=W0611
from .SetCodes import getSetCreationCode # imported from here pylint: disable=W0611
from .DictCodes import getDictionaryCreationCode # imported from here pylint: disable=W0611

from .ParameterParsing import (
    getDirectFunctionEntryPointIdentifier,
    getParameterEntryPointIdentifier,
    getParameterParsingCode,
)

from . import (
    CodeTemplates,
    OperatorCodes,
    CppStrings
)

from nuitka import (
    Variables,
    Constants,
    Builtins,
    Options,
    Utils
)

# pylint: disable=W0622
from ..__past__ import long, unicode, iterItems
# pylint: enable=W0622

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
            return EmptyDictIdentifier()
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

def _defaultToNullIdentifier( identifier ):
    if identifier is not None:
        return identifier
    else:
        return NullIdentifier()

def getReturnCode( identifier, via_exception, context ):
    if via_exception:
        if identifier is None:
            identifier = getConstantHandle(
                context  = context,
                constant = None
            )

        return "throw ReturnValueException( %s );" % identifier.getCodeExportRef()
    else:
        if identifier is not None:
            return "return %s;" % identifier.getCodeExportRef()
        else:
            return "return;"

def getYieldCode( identifier, in_handler ):
    if in_handler:
        return Identifier(
            "YIELD_VALUE_FROM_HANDLER( generator, %s )" % identifier.getCodeExportRef(),
            0
        )
    else:
        return Identifier(
            "YIELD_VALUE( generator, %s )" % identifier.getCodeExportRef(),
            0
        )

def getMetaclassVariableCode( context ):
    assert Utils.python_version < 300

    context.addGlobalVariableNameUsage( "__metaclass__" )

    package_var_identifier = ModuleVariableIdentifier(
        var_name         = "__metaclass__",
        module_code_name = context.getModuleCodeName()
    )

    return "( %s.isInitialized( false ) ? %s : NULL )" % (
        package_var_identifier.getCode(),
        package_var_identifier.getCodeTemporaryRef()
    )

def getBuiltinImportCode( module_identifier, globals_dict, locals_dict, import_list, level ):
    assert type( module_identifier ) is not str
    assert type( globals_dict ) is not str
    assert type( locals_dict ) is not str

    return Identifier(
        "IMPORT_MODULE( %s, %s, %s, %s, %s )" % (
            module_identifier.getCodeTemporaryRef(),
            globals_dict.getCodeTemporaryRef(),
            locals_dict.getCodeTemporaryRef(),
            import_list.getCodeTemporaryRef(),
            level.getCodeTemporaryRef()
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

def _getCallNoStarArgsCode( called_identifier, argument_tuple, argument_dictionary ):
    if argument_dictionary is None:
        if argument_tuple is None:
            return Identifier(
                "CALL_FUNCTION_NO_ARGS( %(function)s )" % {
                    "function"   : called_identifier.getCodeTemporaryRef(),
                },
                1
            )
        else:
            return Identifier(
                "CALL_FUNCTION_WITH_POSARGS( %(function)s, %(pos_args)s )" % {
                    "function"   : called_identifier.getCodeTemporaryRef(),
                    "pos_args"   : argument_tuple.getCodeTemporaryRef()
                },
                1
            )
    else:
        if argument_tuple is None:
            return Identifier(
                "CALL_FUNCTION_WITH_KEYARGS( %(function)s, %(named_args)s )" % {
                    "function"   : called_identifier.getCodeTemporaryRef(),
                    "named_args" : argument_dictionary.getCodeTemporaryRef()
                },
                1
            )
        else:
            return Identifier(
                "CALL_FUNCTION( %(function)s, %(pos_args)s, %(named_args)s )" % {
                    "function"   : called_identifier.getCodeTemporaryRef(),
                    "pos_args"   : argument_tuple.getCodeTemporaryRef(),
                    "named_args" : argument_dictionary.getCodeTemporaryRef()
                },
                1
            )


def getDirectionFunctionCallCode( function_identifier, arguments, closure_variables, extra_arguments, context ):
    function_identifier = getDirectFunctionEntryPointIdentifier(
        function_identifier = function_identifier
    )

    call_args = [
        _defaultToNullIdentifier( extra_argument ).getCodeTemporaryRef()
        for extra_argument in
        extra_arguments
    ]

    call_args += getCodeExportRefs( arguments )

    call_args += getClosureVariableProvisionCode(
        context           = context,
        closure_variables = closure_variables
    )

    return Identifier(
        "%s( %s )" % (
            function_identifier,
            ", ".join( call_args )
        ),
        1
    )


def getCallCode( called_identifier, argument_tuple, argument_dictionary ):
    if argument_dictionary is not None and argument_dictionary.isConstantIdentifier() and \
       argument_dictionary.getConstant() == {}:
        argument_dictionary = None

    if argument_dictionary is None:
        if argument_tuple is None:
            return Identifier(
                "CALL_FUNCTION_NO_ARGS( %(function)s )" % {
                    "function"   : called_identifier.getCodeTemporaryRef(),
                },
                1
            )
        else:
            return Identifier(
                "CALL_FUNCTION_WITH_POSARGS( %(function)s, %(pos_args)s )" % {
                    "function"   : called_identifier.getCodeTemporaryRef(),
                    "pos_args"   : argument_tuple.getCodeTemporaryRef()
                },
                1
            )
    else:
        if argument_tuple is None:
            return Identifier(
                "CALL_FUNCTION_WITH_KEYARGS( %(function)s, %(named_args)s )" % {
                    "function"   : called_identifier.getCodeTemporaryRef(),
                    "named_args" : argument_dictionary.getCodeTemporaryRef()
                },
                1
            )
        else:
            return Identifier(
                "CALL_FUNCTION( %(function)s, %(pos_args)s, %(named_args)s )" % {
                    "function"   : called_identifier.getCodeTemporaryRef(),
                    "pos_args"   : argument_tuple.getCodeTemporaryRef(),
                    "named_args" : argument_dictionary.getCodeTemporaryRef()
                },
                1
            )


def getUnpackNextCode( iterator_identifier, count ):
    return Identifier(
        "UNPACK_NEXT( %s, %d )" % (
            iterator_identifier.getCodeTemporaryRef(),
            count - 1
        ),
        1
    )

def getUnpackCheckCode( iterator_identifier, count ):
    return "UNPACK_ITERATOR_CHECK( %s, %d );" % (
        iterator_identifier.getCodeTemporaryRef(),
        count
    )

def getSpecialAttributeLookupCode( attribute, source ):
    return Identifier(
        "LOOKUP_SPECIAL( %s, %s )" % (
            source.getCodeTemporaryRef(),
            attribute.getCodeTemporaryRef()
        ),
        1
    )

def getAttributeLookupCode( attribute, source ):
    return Identifier(
        "LOOKUP_ATTRIBUTE( %s, %s )" % (
            source.getCodeTemporaryRef(),
            attribute.getCodeTemporaryRef()
        ),
        1
    )

def getAttributeCheckCode( attribute, source ):
    return Identifier(
        "BOOL_FROM( HAS_ATTRIBUTE( %s, %s ) )" % (
            source.getCodeTemporaryRef(),
            attribute.getCodeTemporaryRef()
        ),
        0
    )

def getAttributeCheckBoolCode( attribute, source ):
    return "HAS_ATTRIBUTE( %s, %s )" % (
        source.getCodeTemporaryRef(),
        attribute.getCodeTemporaryRef()
    )

def getAttributeGetCode( attribute, source, default ):
    return Identifier(
        "BUILTIN_GETATTR( %s, %s, %s)" % (
            source.getCodeTemporaryRef(),
            attribute.getCodeTemporaryRef(),
            _defaultToNullIdentifier( default ).getCodeTemporaryRef()
        ),
        1
    )

def getAttributeSetCode( attribute, source, value ):
    return Identifier(
        "( BUILTIN_SETATTR( %s, %s, %s), Py_None )" % (
            source.getCodeTemporaryRef(),
            attribute.getCodeTemporaryRef(),
            value.getCodeTemporaryRef()
        ),
        0
    )


def getImportNameCode( import_name, module ):
    return Identifier(
        "IMPORT_NAME( %s, %s )" % (
            module.getCodeTemporaryRef(),
            import_name.getCodeTemporaryRef()
        ),
        1
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
    if type( codes ) is str:
        assert codes == codes.rstrip(), codes

    return "{\n%s\n}" % indented( codes )

def getOperationCode( operator, identifiers ):
    # This needs to have one return per operation of Python, and there are many of these,
    # pylint: disable=R0911

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
    elif operator == "IPow":
        assert len( identifiers ) == 2

        return Identifier(
            "POWER_OPERATION_INPLACE( %s, %s )" % (
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
    elif operator == "Sub":
        return Identifier(
            "BINARY_OPERATION_SUB( %s, %s )" % (
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif operator == "Div":
        return Identifier(
            "BINARY_OPERATION_DIV( %s, %s )" % (
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif operator == "Mult":
        return Identifier(
            "BINARY_OPERATION_MUL( %s, %s )" % (
                identifier_refs[0],
                identifier_refs[1]
            ),
            1
        )
    elif operator == "Mod":
        return Identifier(
            "BINARY_OPERATION_REMAINDER( %s, %s )" % (
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
        helper, ref_count = OperatorCodes.unary_operator_codes[ operator ]

        return Identifier(
            "UNARY_OPERATION( %s, %s )" % (
                helper,
                identifier_refs[0]
            ),
            ref_count
        )
    else:
        assert False, (operator, identifiers)

def getPrintCode( newline, identifiers, target_file ):
    print_elements_code = []

    for identifier in identifiers:
        print_elements_code.append(
            CodeTemplates.template_print_value % {
                "print_value" : identifier.getCodeTemporaryRef(),
                "target_file" : "target_file" if target_file is not None else "NULL"
            }
        )

    if newline:
        print_elements_code.append(
            CodeTemplates.template_print_newline  % {
                "target_file" : "target_file" if target_file is not None else "NULL"
            }
        )

    if target_file is not None:
        return CodeTemplates.template_print_statement % {
            "target_file"         : _defaultToNullIdentifier( target_file ).getCodeExportRef(),
            "print_elements_code" : indented( print_elements_code )
        }
    else:
        return "\n".join( print_elements_code )


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

def getConditionalExpressionCode( condition_code, identifier_no, identifier_yes ):
    if identifier_yes.getCheapRefCount() == identifier_no.getCheapRefCount():
        if identifier_yes.getCheapRefCount() == 0:
            codes_yes = identifier_yes.getCodeTemporaryRef()
            codes_no  = identifier_no.getCodeTemporaryRef()
            ref_count = 0
        else:
            codes_yes = identifier_yes.getCodeExportRef()
            codes_no  = identifier_no.getCodeExportRef()
            ref_count = 1
    else:
        codes_yes = identifier_yes.getCodeExportRef()
        codes_no  = identifier_no.getCodeExportRef()
        ref_count = 1

    return Identifier(
        CodeTemplates.template_conditional_expression % {
            "condition" : condition_code,
            "yes"       : codes_yes,
            "no"        : codes_no
        },
        ref_count
    )

def getFunctionCreationCode( context, function_identifier, defaults_identifier,
                             kw_defaults_identifier, closure_variables ):
    args = []

    if not kw_defaults_identifier.isConstantIdentifier():
        args.append( kw_defaults_identifier.getCodeExportRef() )

    if not defaults_identifier.isConstantIdentifier():
        args.append( defaults_identifier.getCodeExportRef() )

    args += getClosureVariableProvisionCode(
        context           = context,
        closure_variables = closure_variables
    )

    return CallIdentifier(
        called  = "MAKE_FUNCTION_%s" % function_identifier,
        args    = args
    )

def getBranchCode( condition_code, yes_codes, no_codes ):
    assert yes_codes or no_codes

    if no_codes is None:
        return CodeTemplates.template_branch_one % {
            "condition"   : condition_code,
            "branch_code" : indented( yes_codes if yes_codes is not None else "" )
        }
    else:
        assert no_codes, no_codes

        return CodeTemplates.template_branch_two % {
            "condition"       : condition_code,
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

def getComparisonExpressionCode( comparator, left, right ):
    # There is an awful lot of cases, and it's not helped by the need to generate more
    # complex code in the case of comparison chains. pylint: disable=R0912

    if comparator in OperatorCodes.normal_comparison_codes:
        py_api = OperatorCodes.normal_comparison_codes[ comparator ]

        assert py_api.startswith( "SEQUENCE_CONTAINS" )

        return Identifier(
            "%s( %s, %s )" % (
                py_api,
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            ),
            0
        )
    elif comparator in OperatorCodes.rich_comparison_codes:
        return Identifier(
            "RICH_COMPARE_%s( %s, %s )" % (
                OperatorCodes.rich_comparison_codes[ comparator ],
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            ),
            1
        )
    elif comparator == "Is":
        return Identifier(
            "BOOL_FROM( %s == %s )" % (
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            ),
            0
        )
    elif comparator == "IsNot":
        return Identifier(
            "BOOL_FROM( %s != %s )" % (
                left.getCodeTemporaryRef(),
                right.getCodeTemporaryRef()
            ),
            0
        )

    assert False, comparator

def getComparisonExpressionBoolCode( comparator, left, right ):
    # There is an awful lot of cases, and it's not helped by the need to generate more
    # complex code in the case of comparison chains. pylint: disable=R0912

    if comparator in OperatorCodes.normal_comparison_codes:
        py_api = OperatorCodes.normal_comparison_codes[ comparator ]

        assert py_api.startswith( "SEQUENCE_CONTAINS" )

        comparison = "%s_BOOL( %s, %s )" % (
            py_api,
            left.getCodeTemporaryRef(),
            right.getCodeTemporaryRef()
        )
    elif comparator in OperatorCodes.rich_comparison_codes:
        comparison = "RICH_COMPARE_BOOL_%s( %s, %s )" % (
            OperatorCodes.rich_comparison_codes[ comparator ],
            left.getCodeTemporaryRef(),
            right.getCodeTemporaryRef()
        )
    elif comparator == "Is":
        comparison = "( %s == %s )" % (
            left.getCodeTemporaryRef(),
            right.getCodeTemporaryRef()
        )
    elif comparator == "IsNot":
        comparison = "( %s != %s )" % (
            left.getCodeTemporaryRef(),
            right.getCodeTemporaryRef()
        )
    else:
        assert False, comparator

    return comparison

def getConditionNotBoolCode( condition ):
    return "(!( %s ))" % condition

def getConditionAndCode( operands ):
    return "( %s )" % " && ".join( operands )

def getConditionOrCode( operands ):
    return "( %s )" % " || ".join( operands )

def getConditionSelectionCode( condition_code, yes_code, no_code ):
    return "( %s ) ? ( %s ) : ( %s )" % (
        condition_code,
        yes_code,
        no_code
    )

def getConditionCheckTrueCode( condition ):
    return "CHECK_IF_TRUE( %s )" % condition.getCodeTemporaryRef()

def getConditionCheckFalseCode( condition ):
    return "CHECK_IF_FALSE( %s )" % condition.getCodeTemporaryRef()

def getTrueExpressionCode():
    return "true"

def getFalseExpressionCode():
    return "false"

def getAttributeAssignmentCode( target, attribute, identifier ):
    return "SET_ATTRIBUTE( %s, %s, %s );" % (
        identifier.getCodeTemporaryRef(),
        target.getCodeTemporaryRef(),
        attribute.getCodeTemporaryRef(),
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

def getLineNumberCode( source_ref ):
    if source_ref.shallSetCurrentLine():
        return "frame_guard.setLineNumber( %d );\n" % source_ref.getLineNumber()
    else:
        return ""

def getLoopCode( loop_body_codes, needs_break_exception, needs_continue_exception ):
    if needs_break_exception and needs_continue_exception:
        while_loop_template = CodeTemplates.template_loop_break_continue_catching
        indentation = 2
    elif needs_break_exception:
        while_loop_template = CodeTemplates.template_loop_break_catching
        indentation = 2
    elif needs_continue_exception:
        while_loop_template = CodeTemplates.template_loop_continue_catching
        indentation = 2
    else:
        while_loop_template = CodeTemplates.template_loop_simple
        indentation = 1

    return while_loop_template % {
        "loop_body_codes" : indented(
            loop_body_codes if loop_body_codes is not None else "",
            indentation
        ),
    }

def getVariableAssignmentCode( context, variable, identifier ):
    assert isinstance( variable, Variables.Variable ), variable

    # This ought to be impossible to happen, as an assignment to an overflow variable
    # would have made it a local one.
    assert not variable.isMaybeLocalVariable()

    if variable.isTempVariableReference():
        referenced = variable.getReferenced()

        if not referenced.declared:
            referenced.declared = True

            return getLocalVariableInitCode(
                context   = context,
                variable  = variable.getReferenced(),
                init_from = identifier
            )
        elif not referenced.getNeedsFree():
            # So won't get a reference, and take none, or else it may get lost, which we
            # don't want to happen.

            # This must be true, otherwise the needs no free statement was made in error.
            assert identifier.getCheapRefCount() == 0

            return "%s = %s;" % (
                getVariableCode(
                    variable = variable,
                    context  = context
                ),
                identifier.getCodeTemporaryRef()
            )

    if identifier.getCheapRefCount() == 0:
        identifier_code = identifier.getCodeTemporaryRef()
        assign_code = "assign0"
    else:
        identifier_code = identifier.getCodeExportRef()
        assign_code = "assign1"

    return "%s.%s( %s );" % (
        getVariableCode(
            variable = variable,
            context  = context
        ),
        assign_code,
        identifier_code
    )

def getAssignmentTempKeeperCode( source_identifier, variable, context ):
    ref_count = source_identifier.getCheapRefCount()
    variable_name = variable.getName()

    assert variable.getReferenced().getNeedsFree() == bool( ref_count ), \
           ( variable, variable.getReferenced().getNeedsFree(), ref_count, source_identifier )

    context.addTempKeeperUsage( variable_name, ref_count )

    return Identifier(
        "%s.assign( %s )" % (
            variable_name,
            source_identifier.getCodeExportRef() if ref_count else source_identifier.getCodeTemporaryRef()
        ),
        0
    )

def getTempKeeperHandle( variable, context ):
    variable_name = variable.getName()
    ref_count = context.getTempKeeperRefCount( variable_name )

    if ref_count == 1:
        return Identifier(
            "%s.asObject()" % variable_name,
            1
        )
    else:
        # TODO: Could create an identifier, where 0 is just cheap, and 1 is still
        # available, may give nicer to read code occasionally.
        return Identifier(
            "%s.asObject0()" % variable_name,
            0
        )

def getVariableDelCode( context, tolerant, variable ):
    assert isinstance( variable, Variables.Variable ), variable

    if variable.isModuleVariable():
        var_name = variable.getName()

        context.addGlobalVariableNameUsage( var_name )

        return "_mvar_%s_%s.del( %s );" % (
            context.getModuleCodeName(),
            var_name,
            "true" if tolerant else "false"
        )
    else:
        return "%s.del( %s );" % (
            getVariableCode(
                variable = variable,
                context  = context
            ),
            "true" if tolerant else "false"
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

def getTryFinallyCode( context, needs_continue, needs_break, needs_return_value_catch,
                       needs_return_value_reraise, aborting, code_tried, code_final,
                       try_count ):

    tb_making = getTracebackMakingIdentifier( context )

    rethrow_setups = ""
    rethrow_catchers = ""
    rethrow_raisers = ""

    values = {
        "try_count" : try_count
    }

    if needs_continue:
        rethrow_setups += CodeTemplates.try_finally_template_setup_continue % values
        rethrow_catchers += CodeTemplates.try_finally_template_catch_continue % values
        rethrow_raisers += CodeTemplates.try_finally_template_reraise_continue % values

    if needs_break:
        rethrow_setups += CodeTemplates.try_finally_template_setup_break  % values
        rethrow_catchers += CodeTemplates.try_finally_template_catch_break % values
        rethrow_raisers += CodeTemplates.try_finally_template_reraise_break % values

    if needs_return_value_catch:
        rethrow_setups += CodeTemplates.try_finally_template_setup_return_value % values
        rethrow_catchers += CodeTemplates.try_finally_template_catch_return_value % values

        if needs_return_value_reraise:
            rethrow_raisers += CodeTemplates.try_finally_template_reraise_return_value % values
        elif not aborting:
            rethrow_raisers += CodeTemplates.try_finally_template_indirect_return_value % values
        else:
            rethrow_raisers += CodeTemplates.try_finally_template_direct_return_value % values

    result = CodeTemplates.try_finally_template % {
        "try_count"        : try_count,
        "tried_code"       : indented( code_tried ),
        "final_code"       : indented( code_final, 0 ),
        "tb_making"        : tb_making.getCodeExportRef(),
        "rethrow_setups"   : rethrow_setups,
        "rethrow_catchers" : rethrow_catchers,
        "rethrow_raisers"  : rethrow_raisers,
    }

    if not rethrow_raisers:
        result = result.rstrip()

    return result

def getTryExceptHandlerCode( exception_identifiers, handler_code, needs_frame_detach, first_handler ):
    exception_code = []

    cond_keyword = "if" if first_handler else "else if"

    if exception_identifiers:
        exception_code.append(
            "%s ( %s )" % (
                cond_keyword,
                " || ".join(
                    "_exception.matches( %s )" % exception_identifier.getCodeTemporaryRef()
                    for exception_identifier in
                    exception_identifiers
                )
            )
        )
    else:
        exception_code.append(
            "%s (true)" % cond_keyword
        )

    if handler_code is None:
        handler_code = []

    if needs_frame_detach:
        handler_code.insert( 0, CodeTemplates.template_setup_except_handler_detaching % {} )

    exception_code += getBlockCode(
        handler_code
    ).split( "\n" )

    return exception_code

def getTryExceptCode( context, code_tried, handler_codes ):
    exception_code = handler_codes
    exception_code += CodeTemplates.try_except_reraise_unmatched_template.split( "\n" )

    tb_making = getTracebackMakingIdentifier( context )

    return CodeTemplates.try_except_template % {
        "tried_code"     : indented( code_tried or "" ),
        "exception_code" : indented( exception_code ),
        "guard_class"    : context.getFrameGuardClass(),
        "tb_making"      : tb_making.getCodeExportRef(),
    }

def getTryNextExceptStopIterationIdentifier( context ):
    try_count = context.allocateTryNumber()

    return Identifier( "_tmp_unpack_%d" % try_count, 1 )

def getTryNextExceptStopIterationCode( source_identifier, handler_code, assign_code, temp_identifier ):
    return CodeTemplates.template_try_next_except_stop_iteration % {
        "temp_var"          : temp_identifier.getCode(),
        "handler_code"      : indented( handler_code ),
        "assignment_code"   : assign_code,
        "source_identifier" : source_identifier.getCodeTemporaryRef()
    }



def getRaiseExceptionCode( exception_type_identifier, exception_value_identifier,
                           exception_tb_identifier, exception_cause_identifier,
                           exception_tb_maker ):
    if exception_cause_identifier is not None:
        return "RAISE_EXCEPTION_WITH_CAUSE( %s, %s, %s );" % (
            exception_type_identifier.getCodeExportRef(),
            exception_cause_identifier.getCodeExportRef(),
            exception_tb_maker.getCodeExportRef()
        )
    elif exception_value_identifier is None and exception_tb_identifier is None:
        return "RAISE_EXCEPTION( %s, %s );" % (
            exception_type_identifier.getCodeExportRef(),
            exception_tb_maker.getCodeExportRef()
        )
    elif exception_tb_identifier is None:
        return "RAISE_EXCEPTION( %s, %s, %s );" % (
            exception_type_identifier.getCodeExportRef(),
            exception_value_identifier.getCodeExportRef(),
            exception_tb_maker.getCodeExportRef()
        )
    else:
        return "RAISE_EXCEPTION( %s, %s, %s );" % (
            exception_type_identifier.getCodeExportRef(),
            exception_value_identifier.getCodeExportRef(),
            exception_tb_identifier.getCodeExportRef()
        )

def getReRaiseExceptionCode( local, final ):
    if local:
        thrower_code = CodeTemplates.try_except_reraise_template % {}
    else:
        thrower_code = "RERAISE_EXCEPTION();"

    if final:
        return CodeTemplates.try_except_reraise_finally_template % {
            "try_count"    : final,
            "thrower_code" : thrower_code
        }
    else:
        return thrower_code

def getRaiseExceptionExpressionCode( exception_type_identifier, exception_value_identifier, exception_tb_maker ):
    return ThrowingIdentifier(
        "THROW_EXCEPTION( %s, %s, %s )" % (
            exception_type_identifier.getCodeExportRef(),
            exception_value_identifier.getCodeExportRef(),
            exception_tb_maker.getCodeExportRef()
        )
    )

def getSideEffectsCode( side_effects, identifier ):
    assert side_effects

    side_effects_code = ", ".join(
        side_effect.getCodeTemporaryRef()
        for side_effect in
        side_effects
    )

    if identifier.getCheapRefCount() == 0:
        return Identifier(
            "( %s, %s )" % (
                side_effects_code,
                identifier.getCodeTemporaryRef()
            ),
            0
        )
    else:
        return Identifier(
            "( %s, %s )" % (
                side_effects_code,
                identifier.getCodeExportRef()
            ),
            1
        )

def getBuiltinRefCode( context, builtin_name ):
    return Identifier(
        "LOOKUP_BUILTIN( %s )" % getConstantCode(
            constant = builtin_name,
            context  = context
        ),
        0 if Utils.python_version < 300 else 1
    )

def getBuiltinAnonymousRefCode( builtin_name ):
    return Identifier(
        "(PyObject *)%s" % Builtins.builtin_anon_codes[ builtin_name ],
        0
    )

def getExceptionRefCode( exception_type ):
    if exception_type == "NotImplemented":
        return Identifier(
            "Py_NotImplemented",
            0
        )

    return Identifier(
        "PyExc_%s" % exception_type,
        0
    )

def getMakeBuiltinExceptionCode( context, exception_type, exception_args ):
    return getCallCode(
        called_identifier    = Identifier( "PyExc_%s" % exception_type, 0 ),
        argument_tuple       = getTupleCreationCode(
            element_identifiers = exception_args,
            context             = context,
        ),
        argument_dictionary  = None
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

        include_closure = not provider.isUnoptimized() and not provider.isClassDictCreation()
    else:
        variables = provider.getVariables()

        include_closure = True

    return [
        "%s" % getVariableCode(
            variable = variable,
            context = context
        )
        for variable in
        variables
        if not variable.isModuleVariable()
        if not variable.isMaybeLocalVariable()
        if ( not variable.isClosureReference() or include_closure )
    ]


def getLoadDirCode( context, provider ):
    if provider.isModule():
        # TODO: Giving 1 for a temporary ref looks wrong.
        return Identifier(
            "PyDict_Keys( %s )" % getLoadGlobalsCode(
                context = context
            ).getCodeTemporaryRef(),
            1
        )
    else:
        if context.hasLocalsDict():
            return Identifier(
                "PyDict_Keys( %s )" % getLoadLocalsCode(
                    context  = context,
                    provider = provider,
                    mode     = "updated"
                ),
                1
            )
        else:
            local_list = _getLocalVariableList(
                context  = context,
                provider = provider
            )

            result = getListCreationCode(
                context             = context,
                element_identifiers = (),
            )

            for local_var in local_list:
                result = Identifier(
                    "%s.updateLocalsDir( %s )" % (
                        local_var,
                        result.getCodeTemporaryRef()
                    ),
                    0
                )

            return result

def getLoadVarsCode( identifier ):
    return Identifier(
        "LOOKUP_VARS( %s )" % identifier.getCodeTemporaryRef(),
        1
    )

def getLoadGlobalsCode( context ):
    return Identifier(
        "((PyModuleObject *)%(module_identifier)s)->md_dict" % {
            "module_identifier" : getModuleAccessCode( context )
        },
        0
    )

def getLoadLocalsCode( context, provider, mode ):
    if provider.isModule():
        return getLoadGlobalsCode( context )
    elif not context.hasLocalsDict():
        local_list = _getLocalVariableList(
            provider = provider,
            context  = context
        )

        result = EmptyDictIdentifier()

        for local_var in local_list:
            result = Identifier(
                "%s.updateLocalsDict( %s )" % (
                    local_var,
                    result.getCodeExportRef()
                ),
                1
            )

        return result
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

            result = Identifier(
                "locals_dict.asObject()",
                0
            )

            for local_var in local_list:
                result = Identifier(
                    "%s.updateLocalsDict( %s )" % (
                        local_var,
                        result.getCodeTemporaryRef()
                    ),
                    0
                )

            return result
        else:
            assert False

def getSetLocalsCode( new_locals_identifier ):
    return "locals_dict.assign1( %s );" % new_locals_identifier.getCodeExportRef()

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


def getEvalCode( context, exec_code, filename_identifier, globals_identifier,
                 locals_identifier, mode_identifier, future_flags, provider ):
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

def getExecCode( context, exec_code, globals_identifier, locals_identifier, future_flags, provider, source_ref ):
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

        if Options.isFullCompat():
            filename_identifier = getConstantCode(
                constant = "<string>",
                context  = context
            )
        else:
            filename_identifier = getConstantCode(
                constant = "<string at %s>" % source_ref.getAsString(),
                context  = context
            )


        return CodeTemplates.exec_local_template % {
            "globals_identifier"      : globals_identifier.getCodeExportRef(),
            "locals_identifier"       : locals_identifier.getCodeExportRef(),
            "make_globals_identifier" : make_globals_identifier.getCodeExportRef(),
            "make_locals_identifier"  : make_locals_identifier.getCodeExportRef(),
            "source_identifier"       : exec_code.getCodeTemporaryRef(),
            "filename_identifier"     : filename_identifier,
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

def getBuiltinSuperCode( type_identifier, object_identifier ):
    return Identifier(
        "BUILTIN_SUPER( %s, %s )" % (
            _defaultToNullIdentifier( type_identifier ).getCodeTemporaryRef(),
            _defaultToNullIdentifier( object_identifier ).getCodeTemporaryRef()
        ),
        1
    )

def getBuiltinIsinstanceCode( inst_identifier, cls_identifier ):
    return Identifier(
        "BOOL_FROM( BUILTIN_ISINSTANCE_BOOL( %s, %s ) )" % (
            inst_identifier.getCodeTemporaryRef(),
            cls_identifier.getCodeTemporaryRef()
        ),
        0
    )

def getBuiltinIsinstanceBoolCode( inst_identifier, cls_identifier ):
    return "BUILTIN_ISINSTANCE_BOOL( %s, %s )" % (
        inst_identifier.getCodeTemporaryRef(),
        cls_identifier.getCodeTemporaryRef()
    )

def getBuiltinOpenCode( filename, mode, buffering ):
    return Identifier(
        "OPEN_FILE( %s, %s, %s )" % (
            _defaultToNullIdentifier( filename ).getCodeTemporaryRef(),
            _defaultToNullIdentifier( mode ).getCodeTemporaryRef(),
            _defaultToNullIdentifier( buffering ).getCodeTemporaryRef()
        ),
        1
    )

def getBuiltinLenCode( identifier ):
    return Identifier( "BUILTIN_LEN( %s )" % identifier.getCodeTemporaryRef(), 1 )

def getBuiltinDir1Code( identifier ):
    return Identifier( "BUILTIN_DIR1( %s )" % identifier.getCodeTemporaryRef(), 1 )

def getBuiltinRangeCode( low, high, step ):
    if step is not None:
        return HelperCallIdentifier(
            "BUILTIN_RANGE3", low, high, step
        )
    elif high is not None:
        return HelperCallIdentifier(
            "BUILTIN_RANGE2", low, high
        )
    else:
        return HelperCallIdentifier(
            "BUILTIN_RANGE", low
        )

def getBuiltinChrCode( value ):
    return HelperCallIdentifier( "BUILTIN_CHR", value )

def getBuiltinOrdCode( value ):
    return HelperCallIdentifier( "BUILTIN_ORD", value )

def getBuiltinBinCode( value ):
    return HelperCallIdentifier( "BUILTIN_BIN", value )

def getBuiltinOctCode( value ):
    return HelperCallIdentifier( "BUILTIN_OCT", value )

def getBuiltinHexCode( value ):
    return HelperCallIdentifier( "BUILTIN_HEX", value )

def getBuiltinType1Code( value ):
    return HelperCallIdentifier( "BUILTIN_TYPE1", value )

def getBuiltinIter1Code( value ):
    return HelperCallIdentifier( "MAKE_ITERATOR", value )

def getBuiltinIter2Code( callable_identifier, sentinel_identifier ):
    return Identifier(
        "BUILTIN_ITER2( %s, %s )" % (
            callable_identifier.getCodeExportRef(),
            sentinel_identifier.getCodeExportRef()
        ),
        1
    )

def getBuiltinNext1Code( value ):
    return HelperCallIdentifier( "BUILTIN_NEXT1", value )

def getBuiltinNext2Code( iterator_identifier, default_identifier ):
    return Identifier(
        "BUILTIN_NEXT2( %s, %s )" % (
            iterator_identifier.getCodeTemporaryRef(),
            default_identifier.getCodeTemporaryRef()
        ),
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
    return HelperCallIdentifier( "TO_TUPLE", identifier )

def getBuiltinListCode( identifier ):
    return HelperCallIdentifier( "TO_LIST", identifier )

def getBuiltinDictCode( seq_identifier, dict_identifier ):
    if dict_identifier.isConstantIdentifier() and dict_identifier.getConstant() == {}:
        dict_identifier = None

    assert seq_identifier is not None or dict_identifier is not None

    if seq_identifier is not None:
        return Identifier(
            "TO_DICT( %s, %s )" % (
                seq_identifier.getCodeTemporaryRef(),
                _defaultToNullIdentifier( dict_identifier ).getCodeTemporaryRef()
            ),
            1
        )
    else:
        return dict_identifier

def getBuiltinFloatCode( identifier ):
    return HelperCallIdentifier( "TO_FLOAT", identifier )

def getBuiltinLongCode( context, identifier, base ):
    if identifier is None:
        identifier = getConstantHandle( context = context, constant = "0" )

    if base is None:
        return HelperCallIdentifier( "TO_LONG", identifier )
    else:
        return HelperCallIdentifier( "TO_LONG2", identifier, base )

def getBuiltinIntCode( context, identifier, base ):
    if identifier is None:
        identifier = getConstantHandle( context = context, constant = "0" )

    if base is None:
        return HelperCallIdentifier( "TO_INT", identifier )
    else:
        return HelperCallIdentifier( "TO_INT2", identifier, base )

def getBuiltinStrCode( identifier ):
    return HelperCallIdentifier( "TO_STR", identifier )

def getBuiltinUnicodeCode( identifier, encoding, errors ):
    if encoding is None and errors is None:
        return HelperCallIdentifier(
            "TO_UNICODE",
            identifier
        )
    else:
        return HelperCallIdentifier(
            "TO_UNICODE3",
            identifier,
            encoding,
            errors,
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

def getTracebackMakingIdentifier( context ):
    return Identifier(
        "MAKE_TRACEBACK( %s )" % (
            getFrameMakingIdentifier( context = context ).getCodeExportRef(),
        ),
        1
    )

def getModuleIdentifier( module_name ):
    return module_name.replace( ".", "__" ).replace( "-", "_" )

def getPackageIdentifier( module_name ):
    return module_name.replace( ".", "__" )

def getModuleCode( context, module_name, package_name, codes, tmp_keepers,
                   doc_identifier, path_identifier, other_module_names, source_ref ):

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

    if package_name is None:
        module_inits = CodeTemplates.module_init_no_package_template % {
            "module_identifier"   : module_identifier,
            "filename_identifier" : getConstantCode(
                constant = source_ref.getFilename(),
                context  = context
            ),
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
            "filename_identifier"     : getConstantCode(
                constant = source_ref.getFilename(),
                context  = context
            ),
            "is_package"              : 0 if path_identifier is None else 1,
            "path_identifier"         : path_identifier.getCode() if path_identifier else "",
            "doc_identifier"          : doc_identifier.getCode(),
            "package_identifier"      : getPackageIdentifier( package_name )
        }

    assert module_inits.endswith( "\n" )

    header = CodeTemplates.global_copyright % {
        "name"    : module_name,
        "version" : Options.getVersion()
    }

    # These are for keeping values during evaluation.
    module_local_decl = [
        "PyObjectTempKeeper%s %s;" % ( ref_count, tmp_variable )
        for tmp_variable, ref_count in sorted( iterItems( tmp_keepers ) )
    ]

    # Create for for "inittab" to use in unfreezing of modules if that is used.
    module_inittab = []

    for other_module_name in other_module_names:
        module_inittab.append (
            CodeTemplates.module_inittab_entry % {
                "module_name"       : other_module_name,
                "module_identifier" : getModuleIdentifier( other_module_name ),
            }
        )

    module_code = CodeTemplates.module_body_template % {
        "module_name"           : module_name,
        "module_name_obj"       : getConstantCode(
            context  = context,
            constant = module_name
        ),
        "module_identifier"     : module_identifier,
        "module_functions_decl" : functions_decl,
        "module_functions_code" : functions_code,
        "module_globals"        : module_globals,
        "module_inits"          : module_inits + indented( module_local_decl ),
        "module_code"           : indented( codes ),
        "module_inittab"        : indented( sorted( module_inittab ) ),
        "use_unfreezer"         : 1 if other_module_names else 0
    }

    return header + module_code

def getModuleDeclarationCode( module_name, extra_declarations ):
    module_header_code = CodeTemplates.module_header_template % {
        "module_identifier"  : getModuleIdentifier( module_name ),
        "extra_declarations" : extra_declarations
    }

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__%s_H__" % getModuleIdentifier( module_name ),
        "header_body"       : module_header_code
    }

def getMainCode( codes, code_identifier, context ):
    if code_identifier is None:
        code_identifier = NullIdentifier()

    main_code = CodeTemplates.main_program % {
        "sys_executable"  : getConstantCode(
            constant = "python.exe" if Options.isWindowsTarget() else sys.executable,
            context  = context
        ),
        "code_identifier" : code_identifier.getCodeTemporaryRef()
    }

    return codes + main_code

def getFunctionsCode( context ):
    result = ""

    for _code_name, ( _function_decl, function_code ) in sorted( context.getFunctionsCodes().items() ):
        result += function_code

    return result

def getFunctionsDecl( context ):
    result = ""

    for _code_name, ( function_decl, _function_code ) in sorted( context.getFunctionsCodes().items() ):
        result += function_decl

    return result

def _getFunctionCreationArgs( defaults_identifier, kw_defaults_identifier, closure_variables ):
    result = []

    if not kw_defaults_identifier.isConstantIdentifier():
        result.append( "PyObject *kwdefaults" )

    if not defaults_identifier.isConstantIdentifier():
        result.append( "PyObject *defaults" )


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

def getFunctionDecl( context, function_identifier, defaults_identifier, kw_defaults_identifier,
                     closure_variables, function_parameter_variables ):

    if context.isForCreatedFunction():
        function_creation_arg_spec = _getFunctionCreationArgs(
            defaults_identifier    = defaults_identifier,
            kw_defaults_identifier = kw_defaults_identifier,
            closure_variables      = closure_variables
        )

        function_creation_arg_names = _extractArgNames( function_creation_arg_spec )

        return CodeTemplates.template_function_make_declaration % {
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
    else:
        parameter_objects_decl = [
            "PyObject *_python_par_" + variable.getName()
            for variable in
            function_parameter_variables
        ]

        for closure_variable in closure_variables:
            parameter_objects_decl.append(
                closure_variable.getDeclarationCode()
            )

        direct_call_arg_names = _extractArgNames( parameter_objects_decl )

        result = CodeTemplates.template_function_direct_declaration % {
            "file_scope"               : context.getExportScope(),
            "function_identifier"      : function_identifier,
            "direct_call_arg_names"    : ", ".join( direct_call_arg_names ),
            "direct_call_arg_reversal" : getEvalOrderedCode(
                context = context,
                args    = direct_call_arg_names
            ),
            "direct_call_arg_spec"     : getEvalOrderedCode(
                context = context,
                args    = parameter_objects_decl
            )
        }

        if context.isForCrossModuleUsage():
            context.addExportDeclarations( result )

            return ""
        else:
            return result

def _getFuncDefaultValue( defaults_identifier ):
    if defaults_identifier.isConstantIdentifier():
        return defaults_identifier
    else:
        return Identifier( "defaults", 1 )


def _getFuncKwDefaultValue( kw_defaults_identifier ):
    if kw_defaults_identifier.isConstantIdentifier():
        return kw_defaults_identifier
    else:
        return Identifier( "kwdefaults", 1 )

def getGeneratorFunctionCode( context, function_name, function_identifier, parameters,
                              closure_variables, user_variables, defaults_identifier,
                              kw_defaults_identifier, annotations_identifier, tmp_keepers,
                              function_codes, source_ref, function_doc ):
    # We really need this many parameters here.
    # pylint: disable=R0913

    parameter_variables, entry_point_code, parameter_objects_decl, mparse_identifier = getParameterParsingCode(
        function_identifier     = function_identifier,
        function_name           = function_name,
        parameters              = parameters,
        needs_creation          = context.isForCreatedFunction(),
        context                 = context,
    )

    context_decl = []
    context_copy = []
    context_free = []

    function_parameter_decl = [
        getLocalVariableInitCode(
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
            "_python_context->python_var_%s.setVariableNameAndValue( %s, _python_par_%s );" % (
                variable.getName(),
                getConstantCode(
                    constant = variable.getName(),
                    context = context
                ),
                variable.getName()
            )
        )

    function_var_inits = []
    local_var_decl = []

    for user_variable in user_variables:
        local_var_decl.append(
            getLocalVariableInitCode(
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

    # These are for keeping values during evaluation.
    function_var_inits += [
        "PyObjectTempKeeper%s %s;" % ( ref_count, tmp_variable )
        for tmp_variable, ref_count in sorted( iterItems( tmp_keepers ) )
    ]

    for closure_variable in closure_variables:
        assert closure_variable.isShared()

        context_decl.append(
            getLocalVariableInitCode(
                context    = context,
                variable   = closure_variable,
                in_context = True
            )
        )
        context_copy.append(
            "_python_context->python_closure_%s.shareWith( python_closure_%s );" % (
                closure_variable.getName(),
                closure_variable.getName()
            )
        )

    function_creation_args = _getFunctionCreationArgs(
        defaults_identifier    = defaults_identifier,
        kw_defaults_identifier = kw_defaults_identifier,
        closure_variables      = closure_variables
    )

    function_doc = getConstantCode(
        context  = context,
        constant = function_doc
    )

    function_name_obj = getConstantCode(
        constant = function_name,
        context  = context,
    )

    instance_context_decl = function_parameter_decl + local_var_decl

    if context.isForDirectCall():
        instance_context_decl = context_decl + instance_context_decl
        context_decl = []

    if context_decl:
        result = CodeTemplates.genfunc_context_body_template % {
            "function_identifier"            : function_identifier,
            "function_common_context_decl"   : indented( context_decl ),
            "function_instance_context_decl" : indented( instance_context_decl ),
            "context_free"                   : indented( context_free, 2 ),
        }
    elif instance_context_decl:
        result = CodeTemplates.genfunc_context_local_only_template % {
            "function_identifier"            : function_identifier,
            "function_instance_context_decl" : indented( instance_context_decl )
        }
    else:
        result = ""

    if instance_context_decl or context_decl:
        context_access_instance = CodeTemplates.generator_context_access_template2  % {
            "function_identifier" : function_identifier
        }
    else:
        context_access_instance = ""

    function_locals = []

    if context.hasLocalsDict():
        function_locals += CodeTemplates.function_dict_setup.split( "\n" )

    function_locals += function_var_inits

    result += CodeTemplates.genfunc_yielder_template % {
        "function_identifier" : function_identifier,
        "function_body"       : indented( function_codes, 2 ),
        "function_var_inits"  : indented( function_locals, 2 ),
        "context_access"      : indented( context_access_instance, 2 ),
    }

    code_identifier = context.getCodeObjectHandle(
        filename      = source_ref.getFilename(),
        arg_names     = parameters.getCoArgNames(),
        kw_only_count = parameters.getKwOnlyParameterCount(),
        line_number   = source_ref.getLineNumber(),
        code_name     = function_name,
        is_generator  = True,
        is_optimized  = not context.hasLocalsDict()
    )

    if context_decl or instance_context_decl:
        if context_decl:
            context_making = CodeTemplates.genfunc_common_context_use_template % {
                "function_identifier"        : function_identifier,
            }
        else:
            context_making = CodeTemplates.genfunc_local_context_use_template  % {
                "function_identifier"        : function_identifier,
            }

        context_making = context_making.split( "\n" )

        if context.isForDirectCall():
            context_making += context_copy

        generator_making = CodeTemplates.genfunc_generator_with_context_making  % {
            "function_name_obj"   : function_name_obj,
            "function_identifier" : function_identifier,
            "code_identifier"     : code_identifier.getCodeTemporaryRef()
        }
    else:
        generator_making = CodeTemplates.genfunc_generator_without_context_making  % {
            "function_name_obj"   : function_name_obj,
            "function_identifier" : function_identifier,
            "code_identifier"     : code_identifier.getCodeTemporaryRef()
        }

        context_making = []

    if context.isForDirectCall():
        for closure_variable in closure_variables:
            parameter_objects_decl.append(
                closure_variable.getDeclarationCode()
            )

    result += CodeTemplates.genfunc_function_maker_template % {
        "function_name"              : function_name,
        "function_identifier"        : function_identifier,
        "context_making"             : indented( context_making, 1 ),
        "context_copy"               : indented( parameter_context_assign, 2 ),
        "generator_making"           : generator_making,
        "parameter_objects_decl"     : ", ".join( parameter_objects_decl ),
    }

    func_defaults = _getFuncDefaultValue(
        defaults_identifier = defaults_identifier
    )

    func_kwdefaults = _getFuncKwDefaultValue(
        kw_defaults_identifier = kw_defaults_identifier
    )

    # TODO: Probably should support passing NULL to avoid useless dictionaries.
    if annotations_identifier is None:
        annotations_identifier = getConstantAccess(
            context  = context,
            constant = {}
        )

    if context.isForCreatedFunction():
        result += entry_point_code

        if context_decl:
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
                "code_identifier"            : code_identifier.getCodeTemporaryRef(),
                "function_creation_args"     : getEvalOrderedCode(
                    context = context,
                    args    = function_creation_args
                ),
                "context_copy"               : indented( context_copy ),
                "function_doc"               : function_doc,
                "defaults"                   : func_defaults.getCodeExportRef(),
                "kwdefaults"                 : func_kwdefaults.getCodeExportRef(),
                "annotations"                : annotations_identifier.getCodeExportRef(),
                "module_identifier"          : getModuleAccessCode(
                    context = context
                )
            }
        else:
            result += CodeTemplates.make_genfunc_without_context_template % {
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
                "code_identifier"            : code_identifier.getCodeTemporaryRef(),
                "function_creation_args"     : getEvalOrderedCode(
                    context = context,
                    args    = function_creation_args
                ),
                "function_doc"               : function_doc,
                "defaults"                   : func_defaults.getCodeExportRef(),
                "kwdefaults"                 : func_kwdefaults.getCodeExportRef(),
                "annotations"                : annotations_identifier.getCodeExportRef(),
                "module_identifier"          : getModuleAccessCode(
                    context = context
                ),
            }

    return result

def getFunctionCode( context, function_name, function_identifier, parameters, closure_variables,
                     user_variables, tmp_keepers, defaults_identifier, kw_defaults_identifier,
                     annotations_identifier, function_codes, source_ref, function_doc ):
    # We really need this many parameters here.
    # pylint: disable=R0913

    parameter_variables, entry_point_code, parameter_objects_decl, mparse_identifier = getParameterParsingCode(
        function_identifier     = function_identifier,
        function_name           = function_name,
        parameters              = parameters,
        needs_creation          = context.isForCreatedFunction(),
        context                 = context,
    )

    context_decl = []
    context_copy = []
    context_free = []

    function_parameter_decl = [
        getLocalVariableInitCode(
            context   = context,
            variable  = variable,
            init_from = Identifier( "_python_par_" + variable.getName(), 1 )
        )
        for variable in
        parameter_variables
    ]

    for closure_variable in closure_variables:
        context_decl.append(
            getLocalVariableInitCode(
                context    = context,
                variable   = closure_variable,
                in_context = True
            )
        )

        context_copy.append(
            "_python_context->python_closure_%s.shareWith( python_closure_%s );" % (
                closure_variable.getName(),
                closure_variable.getName()
            )
        )

    function_creation_args = _getFunctionCreationArgs(
        defaults_identifier    = defaults_identifier,
        kw_defaults_identifier = kw_defaults_identifier,
        closure_variables      = closure_variables,
    )

    # User local variable initializations
    local_var_inits = [
        getLocalVariableInitCode(
            context  = context,
            variable = variable
        )
        for variable in
        user_variables
    ]

    # These are for keeping values during evaluation.
    local_var_inits += [
        "PyObjectTempKeeper%s %s;" % ( ref_count, tmp_variable )
        for tmp_variable, ref_count in sorted( iterItems( tmp_keepers ) )
    ]

    function_doc = getConstantCode(
        context  = context,
        constant = function_doc
    )

    function_locals = []

    if context.hasLocalsDict():
        function_locals += CodeTemplates.function_dict_setup.split("\n")

    function_locals += function_parameter_decl + local_var_inits

    result = ""

    if context_decl and context.isForCreatedFunction():
        result += CodeTemplates.function_context_body_template % {
            "function_identifier" : function_identifier,
            "context_decl"        : indented( context_decl ),
            "context_free"        : indented( context_free ),
        }

    if closure_variables and context.isForCreatedFunction():
        context_access_function_impl = CodeTemplates.function_context_access_template % {
            "function_identifier" : function_identifier,
        }
    else:
        context_access_function_impl = str( CodeTemplates.function_context_unused_template )

    function_name_obj = getConstantCode(
        context  = context,
        constant = function_name
    )

    if context.isForDirectCall():
        for closure_variable in closure_variables:
            parameter_objects_decl.append(
                closure_variable.getDeclarationCode()
            )

        result += CodeTemplates.function_direct_body_template % {
            "file_scope"                   : context.getExportScope(),
            "function_identifier"          : function_identifier,
            "context_access_function_impl" : context_access_function_impl,
            "direct_call_arg_spec"         : getEvalOrderedCode(
                context = context,
                args    = parameter_objects_decl
            ),
            "function_locals"              : indented( function_locals ),
            "function_body"                : indented( function_codes ),
        }
    else:
        result += CodeTemplates.function_body_template % {
            "function_identifier"          : function_identifier,
            "context_access_function_impl" : context_access_function_impl,
            "parameter_objects_decl"       : ", ".join( parameter_objects_decl ),
            "function_locals"              : indented( function_locals ),
            "function_body"                : indented( function_codes ),
        }

    if context.isForCreatedFunction():
        result += entry_point_code

    func_defaults = _getFuncDefaultValue(
        defaults_identifier = defaults_identifier
    )

    func_kwdefaults = _getFuncKwDefaultValue(
        kw_defaults_identifier = kw_defaults_identifier
    )

    # TODO: Probably should support passing NULL to avoid useless dictionaries.
    if annotations_identifier is None:
        annotations_identifier = getConstantAccess(
            context  = context,
            constant = {}
        )

    if context.isForCreatedFunction():
        code_identifier = context.getCodeObjectHandle(
            filename      = source_ref.getFilename(),
            arg_names     = parameters.getCoArgNames(),
            kw_only_count = parameters.getKwOnlyParameterCount(),
            line_number   = source_ref.getLineNumber(),
            code_name     = function_name,
            is_generator  = False,
            is_optimized  = not context.hasLocalsDict()
        )

        if context_decl:
            result += CodeTemplates.make_function_with_context_template % {
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
                "code_identifier"            : code_identifier.getCodeTemporaryRef(),
                "context_copy"               : indented( context_copy ),
                "function_doc"               : function_doc,
                "defaults"                   : func_defaults.getCodeExportRef(),
                "kwdefaults"                 : func_kwdefaults.getCodeExportRef(),
                "annotations"                : annotations_identifier.getCodeExportRef(),
                "module_identifier"          : getModuleAccessCode( context = context ),
            }
        else:
            result += CodeTemplates.make_function_without_context_template % {
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
                "code_identifier"            : code_identifier.getCodeTemporaryRef(),
                "function_doc"               : function_doc,
                "defaults"                   : func_defaults.getCodeExportRef(),
                "kwdefaults"                 : func_kwdefaults.getCodeExportRef(),
                "annotations"                : annotations_identifier.getCodeExportRef(),
                "module_identifier"          : getModuleAccessCode( context = context ),
            }

    return result


def getSelectMetaclassCode( metaclass_identifier, bases_identifier, context ):
    if Utils.python_version < 300:
        assert metaclass_identifier is None

        args = [
            bases_identifier.getCodeTemporaryRef(),
            getMetaclassVariableCode( context = context )
        ]
    else:
        args = [
            metaclass_identifier.getCodeTemporaryRef(),
            bases_identifier.getCodeTemporaryRef()
        ]


    return CallIdentifier(
        "SELECT_METACLASS",
        args,
    )

def getStatementTrace( source_desc, statement_repr ):
    return 'puts( "Execute: %s " %s );' % (
        source_desc,
        CppStrings.encodeString( statement_repr )
    )


def _getConstantsDeclarationCode( context, for_header ):
    statements = []

    for _code_object_key, code_identifier in context.getCodeObjects():
        declaration = "PyCodeObject *%s;" % code_identifier.getCode()

        if for_header:
            declaration = "extern " + declaration

        statements.append( declaration )

    for _constant_desc, constant_identifier in context.getConstants():
        declaration = "PyObject *%s;" % constant_identifier

        if for_header:
            declaration = "extern " + declaration

        statements.append( declaration )

    return "\n".join( statements )

# TODO: The determation of this should already happen in Building or in a helper not
# during code generation.
_match_attribute_names = re.compile( r"[a-zA-Z_][a-zA-Z0-9_]*$" )

def _isAttributeName( value ):
    return _match_attribute_names.match( value )

def _getUnstreamCode( constant_value, constant_identifier ):
    saved = getStreamedConstant(
        constant_value = constant_value
    )

    assert type( saved ) is bytes

    return "%s = UNSTREAM_CONSTANT( %s, %d );" % (
        constant_identifier,
        CppStrings.encodeString( saved ),
        len( saved )
    )

def _getConstantsDefinitionCode( context ):
    # There are many cases for constants to be created in the most efficient way,
    # pylint: disable=R0912

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

            continue

        if constant_type is tuple and constant_value == ():
            statements.append(
                "%s = PyTuple_New( 0 );" % constant_identifier
            )

            continue

        if constant_type is list and constant_value == []:
            statements.append(
                "%s = PyList_New( 0 );" % constant_identifier
            )

            continue

        if constant_type is set and constant_value == set():
            statements.append(
                "%s = PySet_New( NULL );" % constant_identifier
            )

            continue

        if constant_type is str:
            if str is not unicode:
                statements.append(
                    '%s = UNSTREAM_STRING( %s, %d, %d );assert( %s );' % (
                        constant_identifier,
                        CppStrings.encodeString( constant_value ),
                        len( constant_value ),
                        1 if _isAttributeName( constant_value ) else 0,
                        constant_identifier
                    )
                )

                continue
            else:
                try:
                    encoded = constant_value.encode( "utf-8" )

                    statements.append(
                        '%s = UNSTREAM_STRING( %s, %d, %d );assert( %s );' % (
                            constant_identifier,
                            CppStrings.encodeString( encoded ),
                            len( encoded ),
                            1 if _isAttributeName( constant_value ) else 0,
                            constant_identifier
                        )
                    )

                    continue
                except UnicodeEncodeError:
                    pass

        if constant_value is None:
            continue

        if constant_value is False:
            continue

        if constant_value is True:
            continue

        if constant_type in ( tuple, list, float, complex, unicode, int, long, dict, frozenset, set, bytes, range ):
            statements.append(
                _getUnstreamCode( constant_value, constant_identifier )
            )

            continue

        assert False, (type(constant_value), constant_value, constant_identifier)

    for code_object_key, code_identifier in context.getCodeObjects():
        co_flags = []

        if code_object_key[2] != 0:
            co_flags.append( "CO_NEWLOCALS" )

        if code_object_key[5]:
            co_flags.append( "CO_GENERATOR" )

        if code_object_key[6]:
            co_flags.append( "CO_OPTIMIZED" )

        if Utils.python_version < 300:
            code = "%s = MAKE_CODEOBJ( %s, %s, %d, %s, %d, %s );" % (
                code_identifier.getCode(),
                getConstantCode(
                    constant = code_object_key[0],
                    context  = context
                ),
                getConstantCode(
                    constant = code_object_key[1],
                    context  = context
                ),
                code_object_key[2],
                getConstantCode(
                    constant = code_object_key[3],
                    context  = context
                ),
                len( code_object_key[3] ),
                " | ".join( co_flags ) or "0",
            )
        else:
            code = "%s = MAKE_CODEOBJ( %s, %s, %d, %s, %d, %d, %s );" % (
                code_identifier.getCode(),
                getConstantCode(
                    constant = code_object_key[0],
                    context  = context
                ),
                getConstantCode(
                    constant = code_object_key[1],
                    context  = context
                ),
                code_object_key[2],
                getConstantCode(
                    constant = code_object_key[3],
                    context  = context
                ),
                len( code_object_key[3] ),
                code_object_key[4],
                " | ".join( co_flags ) or  "0",
            )


        statements.append( code )

    return indented( statements )

def getReversionMacrosCode( context ):
    reverse_macros = []
    noreverse_macros = []

    for value in sorted( context.getEvalOrdersUsed() ):
        assert type( value ) is int

        reverse_macro = CodeTemplates.template_reverse_macro % {
            "count"    : value,
            "args"     : ", ".join(
                "arg%s" % (d+1) for d in range( value )
            ),
            "expanded" : ", ".join(
                "arg%s" % (d+1) for d in reversed( range( value ) )
            )
        }

        reverse_macros.append( reverse_macro.rstrip() )

        noreverse_macro = CodeTemplates.template_noreverse_macro % {
            "count"    : value,
            "args"     : ", ".join(
                "arg%s" % (d+1) for d in range( value )
            )
        }

        noreverse_macros.append( noreverse_macro.rstrip() )

    reverse_macros_declaration = CodeTemplates.template_reverse_macros_declaration % {
        "reverse_macros"   : "\n".join( reverse_macros ),
        "noreverse_macros" : "\n".join( noreverse_macros )
    }

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_REVERSES_H__",
        "header_body"       : reverse_macros_declaration
    }

def getMakeTuplesCode( context ):
    make_tuples_codes = []

    for arg_count in context.getMakeTuplesUsed():
        add_elements_code = []

        for arg_index in range( arg_count ):
            add_elements_code.append(
                CodeTemplates.template_add_tuple_element_code % {
                    "tuple_index" : arg_index,
                    "tuple_value" : "element%d" % arg_index
                }
            )

        make_tuples_codes.append(
            CodeTemplates.template_make_tuple_function % {
                "argument_count"             : arg_count,
                "args"                       : ", ".join(
                    "arg%s" % (arg_index+1) for arg_index in range( arg_count )
                ),
                "argument_decl"              : ", ".join(
                    "PyObject *element%d" % arg_index
                    for arg_index in
                    range( arg_count )
                ),
                "add_elements_code"          : "\n".join( add_elements_code ),
            }
        )

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_TUPLES_H__",
        "header_body"       : "\n".join( make_tuples_codes )
    }

def getMakeListsCode( context ):
    make_lists_codes = []

    for arg_count in context.getMakeListsUsed():
        add_elements_code = []

        for arg_index in range( arg_count ):
            add_elements_code.append(
                CodeTemplates.template_add_list_element_code % {
                    "list_index" : arg_index,
                    "list_value" : "element%d" % arg_index
                }
            )

        make_lists_codes.append(
            CodeTemplates.template_make_list_function % {
                "argument_count"             : arg_count,
                "args"                       : ", ".join(
                    "arg%s" % (arg_index+1) for arg_index in range( arg_count )
                ),
                "argument_decl"              : ", ".join(
                    "PyObject *element%d" % arg_index
                    for arg_index in
                    range( arg_count )
                ),
                "add_elements_code"          : "\n".join( add_elements_code ),
            }
        )

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_LISTS_H__",
        "header_body"       : "\n".join( make_lists_codes )
    }

def getMakeDictsCode( context ):
    make_dicts_codes = []

    for arg_count in context.getMakeDictsUsed():
        add_elements_code = []

        for arg_index in range( arg_count ):
            add_elements_code.append(
                CodeTemplates.template_add_dict_element_code % {
                    "dict_key"   : "key%d" % ( arg_index + 1 ),
                    "dict_value" : "value%d" % ( arg_index + 1 )
                }
            )

        make_dicts_codes.append(
            CodeTemplates.template_make_dict_function % {
                "pair_count"                 : arg_count,
                "argument_count"             : arg_count * 2,
                "args"                       : ", ".join(
                    "value%(index)d, key%(index)d" % { "index" : (arg_index+1) }
                    for arg_index in
                    range( arg_count )
                ),
                "argument_decl"              : ", ".join(
                    "PyObject *value%(index)d, PyObject *key%(index)d" % { "index" : (arg_index+1) }
                    for arg_index in
                    range( arg_count )
                ),
                "add_elements_code"          : "\n".join( add_elements_code ),
            }
        )

    return CodeTemplates.template_header_guard % {
        "header_guard_name" : "__NUITKA_DICTS_H__",
        "header_body"       : "\n".join( make_dicts_codes )
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

def getCurrentExceptionTypeCode():
    return Identifier(
        "_exception.getType()",
        0
    )

def getCurrentExceptionValueCode():
    return Identifier(
        "_exception.getValue()",
        0
    )

def getCurrentExceptionTracebackCode():
    return Identifier(
        "(PyObject *)_exception.getTraceback()",
        0
    )

def getListOperationAppendCode( list_identifier, value_identifier ):
    return Identifier(
        "APPEND_TO_LIST( %s, %s ), Py_None" % (
            list_identifier.getCodeTemporaryRef(),
            value_identifier.getCodeTemporaryRef()
        ),
        0
    )

def getSetOperationAddCode( set_identifier, value_identifier ):
    return Identifier(
        "ADD_TO_SET( %s, %s ), Py_None" % (
            set_identifier.getCodeTemporaryRef(),
            value_identifier.getCodeTemporaryRef()
        ),
        0
    )

def getDictOperationSetCode( dict_identifier, key_identifier, value_identifier ):
    return Identifier(
        "DICT_SET_ITEM( %s, %s, %s ), Py_None" % (
            dict_identifier.getCodeTemporaryRef(),
            key_identifier.getCodeTemporaryRef(),
            value_identifier.getCodeTemporaryRef()
        ),
        0
    )

def getDictOperationGetCode( dict_identifier, key_identifier ):
    return Identifier(
        "DICT_GET_ITEM( %s, %s )" % (
            dict_identifier.getCodeTemporaryRef(),
            key_identifier.getCodeTemporaryRef(),
        ),
        1
    )

def getDictOperationRemoveCode( dict_identifier, key_identifier ):
    return "DICT_REMOVE_ITEM( %s, %s );" % (
        dict_identifier.getCodeTemporaryRef(),
        key_identifier.getCodeTemporaryRef()
    )

def getFrameLocalsUpdateCode( locals_identifier ):
    if locals_identifier.isConstantIdentifier() and locals_identifier.getConstant() == {}:
        return ""
    else:
        return CodeTemplates.template_frame_locals_update % {
            "locals_identifier" : locals_identifier.getCodeExportRef()
        }

def getFrameGuardHeavyCode( frame_identifier, code_identifier, codes, locals_code, context ):
    if context.isForDirectCall():
        return_code = CodeTemplates.frame_guard_cpp_return
    else:
        return_code = CodeTemplates.frame_guard_python_return

    tb_making = getTracebackMakingIdentifier( context )

    return CodeTemplates.frame_guard_full_template % {
        "frame_identifier"  : frame_identifier,
        "code_identifier"   : code_identifier.getCodeTemporaryRef(),
        "codes"             : indented( codes ),
        "module_identifier" : getModuleAccessCode( context = context ),
        "frame_locals"      : indented( locals_code, vert_block = True ),
        "tb_making"         : tb_making.getCodeExportRef(),
        "return_code"       : return_code
    }

def getFrameGuardOnceCode( frame_identifier, code_identifier, locals_identifier, codes, context ):
    tb_making = getTracebackMakingIdentifier( context )

    return CodeTemplates.frame_guard_once_template % {
        "frame_identifier"  : frame_identifier,
        "code_identifier"   : code_identifier.getCodeTemporaryRef(),
        "codes"             : indented( codes ),
        "module_identifier" : getModuleAccessCode( context = context ),
        "frame_locals"      : locals_identifier.getCodeExportRef(),
        "tb_making"         : tb_making.getCodeExportRef(),
        "return_code"       : indented( context.getReturnCode() )
    }

def getFrameGuardLightCode( frame_identifier, code_identifier, codes, context ):
    tb_making = getTracebackMakingIdentifier( context )

    return CodeTemplates.frame_guard_genfunc_template % {
        "frame_identifier"  : frame_identifier,
        "code_identifier"   : code_identifier.getCodeTemporaryRef(),
        "codes"             : indented( codes ),
        "module_identifier" : getModuleAccessCode( context = context ),
        "tb_making"         : tb_making.getCodeExportRef(),
    }

def getFrameGuardVeryLightCode( codes ):
    return CodeTemplates.frame_guard_listcontr_template % {
        "codes"             : indented( codes, 0 ),
    }
