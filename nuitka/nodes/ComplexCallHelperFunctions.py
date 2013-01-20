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
""" This module is providing helper functions for complex call re-formulations.

One for each type of call. """

from .FunctionNodes import CPythonExpressionFunctionBody, CPythonExpressionFunctionCreation, CPythonExpressionFunctionCall, CPythonExpressionFunctionRef
from .StatementNodes import CPythonStatementsSequence, CPythonStatementsFrame
from .TypeNode import CPythonExpressionBuiltinIsinstance, CPythonExpressionBuiltinType1
from .BuiltinReferenceNodes import CPythonExpressionBuiltinRef, CPythonExpressionBuiltinExceptionRef, CPythonExpressionBuiltinAnonymousRef
from .ConditionalNodes import CPythonStatementConditional
from .VariableRefNode import CPythonExpressionVariableRef, CPythonExpressionTargetVariableRef, CPythonStatementTempBlock
from .CallNode import CPythonExpressionCallNoKeywords
from .ReturnNode import CPythonStatementReturn
from .TryNodes import CPythonStatementTryExcept, CPythonStatementExceptHandler
from .AssignNodes import CPythonStatementAssignmentVariable
from .ExceptionNodes import CPythonStatementRaiseException, CPythonExpressionBuiltinMakeException
from .ConstantRefNode import CPythonExpressionConstantRef
from .AttributeNodes import CPythonExpressionAttributeLookup
from .ContainerMakingNodes import CPythonExpressionMakeTuple
from .BuiltinTypeNodes import CPythonExpressionBuiltinTuple
from .OperatorNodes import CPythonExpressionOperationBinary

from .ParameterSpec import ParameterSpec

from ..SourceCodeReferences import fromFilename
from .FutureSpec import FutureSpec

function_callable_name_desc = None

source_ref = fromFilename( "internal", FutureSpec() ).atInternal()

from nuitka.Utils import python_version

def getCallableNameDescBody( provider ):
    global function_callable_name_desc

    if function_callable_name_desc is not None:
        return function_callable_name_desc

    helper_name = "get_callable_name_desc"

    result = CPythonExpressionFunctionBody(
        provider   = provider, # We shouldn't need that.
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = ( "called", ),
            list_star_arg = None,
            dict_star_arg = None,
            default_count = 0,
            kw_only_args  = ()
        ),
        source_ref = source_ref,
        is_class   = False
    )

    # Equivalent of:
    #
    # Note: The "called_type" is a temporary variable.
    #
    # called_type = type( BuiltinFunctionType )
    #
    # if ininstance( called, ( FunctionType, MethodType, BuiltinFunctionType ) ):
    #     return called.__name__
    # elif python_version < 3 and isinstance( called, ClassType ):
    #     return called_type.__name__ + " constructor"
    # elif python_version < 3 and isinstance( called, InstanceType ):
    #     return called_type.__name__ + " instance"
    # else:
    #     return called_type.__name__ + " object"

    called_variable, = result.getParameters().getAllVariables()

    def makeCalledVariableRef():
        variable_ref = CPythonExpressionVariableRef(
            variable_name = called_variable.getName(),
            source_ref    = source_ref
        )

        variable_ref.setVariable( called_variable )

        return variable_ref

    def makeNameAttributeLookup( node, attribute_name = "__name__" ):
        return CPythonExpressionAttributeLookup(
            expression     = node,
            attribute_name = attribute_name,
            source_ref     = source_ref
        )

    temp_block = CPythonStatementTempBlock(
        source_ref = source_ref
    )

    functions_case = CPythonStatementsSequence(
        statements = (
            CPythonStatementReturn(
                expression = CPythonExpressionOperationBinary(
                    operator   = "Add",
                    right      = CPythonExpressionConstantRef(
                        constant = "()",
                        source_ref = source_ref
                    ),
                    left       = makeNameAttributeLookup(
                        makeCalledVariableRef()
                    ),
                    source_ref = source_ref

                ),
                source_ref = source_ref
            ),
        ),
        source_ref = source_ref
    )

    no_branch = CPythonStatementsSequence(
        statements = (
            CPythonStatementReturn(
                expression = CPythonExpressionOperationBinary(
                    operator   = "Add",
                    right      = CPythonExpressionConstantRef(
                        constant = " object",
                        source_ref = source_ref
                    ),
                    left       = makeNameAttributeLookup(
                        CPythonExpressionBuiltinType1(
                            value      = makeCalledVariableRef(),
                            source_ref = source_ref
                        )
                    ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
        ),
        source_ref = source_ref
    )

    if python_version < 300:
        instance_case = CPythonStatementsSequence(
            statements = (
                CPythonStatementReturn(
                    expression = CPythonExpressionOperationBinary(
                        operator   = "Add",
                        right      = CPythonExpressionConstantRef(
                            constant = " instance",
                            source_ref = source_ref
                        ),
                        left       = makeNameAttributeLookup(
                            makeNameAttributeLookup(
                                makeCalledVariableRef(),
                                attribute_name = "__class__",
                            )
                        ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
            ),
            source_ref = source_ref
        )

        no_branch = CPythonStatementsSequence(
            statements = (
                CPythonStatementConditional(
                    condition  = CPythonExpressionBuiltinIsinstance(
                        instance   = makeCalledVariableRef(),
                        cls        = CPythonExpressionBuiltinAnonymousRef(
                            builtin_name = "instance",
                            source_ref   = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    yes_branch = instance_case,
                    no_branch  = no_branch,
                    source_ref = source_ref
                ),
            ),
            source_ref = source_ref
        )

        class_case = CPythonStatementsSequence(
            statements = (
                CPythonStatementReturn(
                    expression = CPythonExpressionOperationBinary(
                        operator   = "Add",
                        right      = CPythonExpressionConstantRef(
                            constant = " constructor",
                            source_ref = source_ref
                        ),
                        left       = makeNameAttributeLookup(
                            makeCalledVariableRef(),
                        ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
            ),
            source_ref = source_ref
        )

        no_branch = CPythonStatementsSequence(
            statements = (
                CPythonStatementConditional(
                    condition  = CPythonExpressionBuiltinIsinstance(
                        instance   = makeCalledVariableRef(),
                        cls        = CPythonExpressionBuiltinAnonymousRef(
                            builtin_name = "classobj",
                            source_ref   = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    yes_branch = class_case,
                    no_branch  = no_branch,
                    source_ref = source_ref
                ),
            ),
            source_ref = source_ref
        )

    if python_version < 300:
        normal_cases = ( "function", "builtin_function_or_method", "instancemethod" )
    else:
        normal_cases = ( "function", "builtin_function_or_method" )

    statements = (
        CPythonStatementConditional(
            condition = CPythonExpressionBuiltinIsinstance(
                instance   = makeCalledVariableRef(),
                cls        = CPythonExpressionMakeTuple(
                    elements   = tuple(
                        CPythonExpressionBuiltinAnonymousRef(
                            builtin_name = builtin_name,
                            source_ref   = source_ref
                        )
                        for builtin_name in
                        normal_cases
                    ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            yes_branch = functions_case,
            no_branch  = no_branch,
            source_ref = source_ref
        ),
    )

    temp_block.setBody(
        CPythonStatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    result.setBody(
        CPythonStatementsSequence(
            statements = ( temp_block, ),
            source_ref = source_ref
        )
    )

    function_callable_name_desc = result

    return result

function_call_helper_star_list_only = None

def getFunctionCallHelperStarListOnly( provider ):
    global function_call_helper_star_list_only

    if function_call_helper_star_list_only is not None:
        return function_call_helper_star_list_only

    helper_name = "complex_call_helper_star_list_only"

    # Only need to check if the star argument value is a sequence and then convert to tuple.
    result = CPythonExpressionFunctionBody(
        provider   = provider, # We shouldn't need that.
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = ( "called", "star_arg_list" ),
            list_star_arg = None,
            dict_star_arg = None,
            default_count = 0,
            kw_only_args  = ()
        ),
        source_ref = source_ref,
        is_class   = False
    )

    called_variable, star_arg_list_variable = result.getParameters().getAllVariables()

    def makeListArgVariableRef( assign ):
        variable_ref_class = CPythonExpressionTargetVariableRef if assign else CPythonExpressionVariableRef

        variable_ref = variable_ref_class(
            variable_name = star_arg_list_variable.getName(),
            source_ref    = source_ref
        )

        variable_ref.setVariable( star_arg_list_variable )

        return variable_ref

    def makeCalledVariableRef():
        variable_ref = CPythonExpressionVariableRef(
            variable_name = called_variable.getName(),
            source_ref    = source_ref
        )

        variable_ref.setVariable( called_variable )

        return variable_ref

    # Equivalent of:
    #
    # Note: Call in here is not the same, as it can go without checks directly to PyObject_Call.
    #
    # if not isinstance( star_arg_list, tuple ):
    #     try:
    #         star_arg_list = tuple( star_arg_list )
    #     except TypeError:
    #         raise TypeError, "%s argument after * must be a sequence, not %s" % (
    #             get_callable_name_desc( function ),
    #             type( star_arg_list ).__name__
    #         )
    #
    # return called( *star_arg_list )

    raise_statement = CPythonStatementRaiseException(
        exception_type  = CPythonExpressionBuiltinMakeException(
            exception_name = "TypeError",
            args           = (
                CPythonExpressionOperationBinary(
                    operator = "Mod",
                    left     =  CPythonExpressionConstantRef(
                        constant   = "%s argument after * must be a sequence, not %s",
                        source_ref = source_ref
                    ),
                    right = CPythonExpressionMakeTuple(
                        elements = (
                            CPythonExpressionFunctionCall(
                                function   = CPythonExpressionFunctionCreation(
                                    function_ref = CPythonExpressionFunctionRef(
                                        function_body = getCallableNameDescBody( provider = provider ),
                                        source_ref    = source_ref
                                    ),
                                    defaults     = (),
                                    kw_defaults  = None,
                                    annotations  = None,
                                    source_ref   = source_ref
                                ),
                                values     = (
                                    makeCalledVariableRef(),
                                ),
                                source_ref = source_ref
                            ),
                            CPythonExpressionAttributeLookup(
                                expression = CPythonExpressionBuiltinType1(
                                    value = makeListArgVariableRef( False ),
                                    source_ref = source_ref
                                ),
                                attribute_name = "__name__",
                                source_ref     = source_ref
                            )
                        ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
            ),
            source_ref = source_ref
        ),
        exception_value = None,
        exception_trace = None,
        exception_cause = None,
        source_ref      = source_ref
    )

    handler = CPythonStatementExceptHandler(
        exception_types = (
            CPythonExpressionBuiltinExceptionRef(
                exception_name = "TypeError",
                source_ref     = source_ref
            ),
        ),
        body           = CPythonStatementsSequence(
            statements = (
                raise_statement,
            ),
            source_ref = source_ref
        ),
        source_ref     = source_ref
    )

    statements = (
        CPythonStatementConditional(
            condition  = CPythonExpressionBuiltinIsinstance(
                instance   = makeListArgVariableRef( assign = False ),
                cls        = CPythonExpressionBuiltinRef(
                    builtin_name = "tuple",
                    source_ref   = source_ref
                ),
                source_ref = source_ref
            ),
            yes_branch = None,
            no_branch  = CPythonStatementsSequence(
                statements = (
                    CPythonStatementTryExcept(
                        tried      = CPythonStatementsSequence(
                            statements = (
                                CPythonStatementAssignmentVariable(
                                    variable_ref = makeListArgVariableRef( assign = True ),
                                    source       = CPythonExpressionBuiltinTuple(
                                        value      = makeListArgVariableRef( assign = False ),
                                        source_ref = source_ref
                                    ),
                                    source_ref   = source_ref
                                ),
                            ),
                            source_ref = source_ref
                        ),
                        handlers   = ( handler, ),
                        source_ref = source_ref
                    ),
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        CPythonStatementReturn(
            expression = CPythonExpressionCallNoKeywords(
                called     = makeCalledVariableRef(),
                args       = makeListArgVariableRef( assign = False ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    # TODO: Code generation should become capable of not generating actual exceptions for the
    # TypeError caught immediately and then unused, then the frame will be unnecessary.
    result.setBody(
        CPythonStatementsFrame(
            code_name     = "unused",
            guard_mode    = "pass_through",
            arg_names     = (),
            kw_only_count = 0,
            statements    = statements,
            source_ref    = source_ref
        )
    )

    function_call_helper_star_list_only = result

    return result
