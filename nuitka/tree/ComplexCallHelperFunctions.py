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

from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionBody,
    ExpressionFunctionCreation,
    ExpressionFunctionCall,
    ExpressionFunctionRef
)
from nuitka.nodes.StatementNodes import (
    StatementsSequence,
    StatementsFrame
)
from nuitka.nodes.LoopNodes import (
    StatementLoop,
    StatementBreakLoop
)
from nuitka.nodes.TypeNodes import (
    ExpressionBuiltinIsinstance,
    ExpressionBuiltinType1
)
from nuitka.nodes.BuiltinRefNodes import (
    ExpressionBuiltinAnonymousRef,
    ExpressionBuiltinRef
)
from nuitka.nodes.ConditionalNodes import StatementConditional
from nuitka.nodes.ComparisonNodes import ExpressionComparison
from nuitka.nodes.VariableRefNodes import (
    ExpressionTargetTempVariableRef,
    ExpressionTargetVariableRef,
    ExpressionTempVariableRef,
    ExpressionVariableRef
)
from nuitka.nodes.CallNodes import (
    ExpressionCallKeywordsOnly,
    ExpressionCallNoKeywords,
    ExpressionCallEmpty,
    ExpressionCall
)
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementAssignmentSubscript
)
from nuitka.nodes.ExceptionNodes import (
    StatementRaiseException,
    ExpressionBuiltinMakeException
)
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.AttributeNodes import ExpressionAttributeLookup
from nuitka.nodes.ContainerMakingNodes import ExpressionMakeTuple
from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinTuple
from nuitka.nodes.OperatorNodes import (
    ExpressionOperationBinary,
    ExpressionOperationNOT
)
from nuitka.nodes.BuiltinIteratorNodes import (
    ExpressionBuiltinIter1,
    ExpressionBuiltinNext1
)
from nuitka.nodes.SubscriptNodes import ExpressionSubscriptLookup
from nuitka.nodes.BuiltinDictNodes import ExpressionBuiltinDict
from nuitka.nodes.ModuleNodes import PythonInternalModule

from nuitka.nodes.ParameterSpecs import ParameterSpec
from nuitka.nodes.FutureSpecs import FutureSpec

from nuitka.SourceCodeReferences import fromFilename

from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode
from .VariableClosure import completeVariableClosures
from .Helpers import makeStatementsSequenceFromStatement

source_ref = fromFilename( "internal", FutureSpec() ).atInternal()

from nuitka.Utils import python_version

# Cache result. TODO: no more as special as it used to be, maybe can be found in
# stdlib.
def once_decorator( func ):
    func.cached_value = None

    def replacement():
        if func.cached_value is None:
            func.cached_value = func()

        return func.cached_value

    return replacement


internal_module = None

def getInternalModule():
    # Using global here, as this is really a about the internal module as a
    # singleton, pylint: disable=W0603
    global internal_module

    if internal_module is None:
        internal_module = PythonInternalModule()

    return internal_module

def makeCalledVariableRef():
    variable_ref = ExpressionVariableRef(
        variable_name = "called",
        source_ref    = source_ref
    )

    return variable_ref

def makeArgsVariableRef():
    variable_ref = ExpressionVariableRef(
        variable_name = "args",
        source_ref    = source_ref
    )

    return variable_ref

def makeKwVariableRef( assign ):
    variable_ref_class = ExpressionTargetVariableRef if assign else ExpressionVariableRef

    variable_ref = variable_ref_class(
        variable_name = "kw",
        source_ref    = source_ref
    )

    return variable_ref

def makeStarListArgVariableRef( assign ):
    variable_ref_class = ( ExpressionTargetVariableRef
                             if assign else
                           ExpressionVariableRef )

    variable_ref = variable_ref_class(
        variable_name = "star_arg_list",
        source_ref    = source_ref
    )

    return variable_ref

def makeStarDictArgVariableRef( assign ):
    variable_ref_class = ( ExpressionTargetVariableRef
                             if assign else
                           ExpressionVariableRef )

    variable_ref = variable_ref_class(
        variable_name = "star_arg_dict",
        source_ref    = source_ref
    )

    return variable_ref

# TODO: Code generation should become capable of not generating actual
# exceptions for the TypeError caught immediately and then unused, then the
# frame will be unnecessary.

def makePseudoFrame( parameters, statements ):
    return StatementsFrame(
        code_name     = "unused",
        guard_mode    = "pass_through",
        var_names     = parameters.getParameterNames(),
        arg_count     = parameters.getArgumentCount(),
        has_starlist  = parameters.getStarListArgumentName() is not None,
        has_stardict  = parameters.getStarDictArgumentName() is not None,
        kw_only_count = 0,
        statements    = statements,
        source_ref    = source_ref
    )


@once_decorator
def getCallableNameDescBody():
    helper_name = "get_callable_name_desc"

    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
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
    # if ininstance( called, (FunctionType, MethodType, BuiltinFunctionType) ):
    #     return called.__name__
    # elif python_version < 3 and isinstance( called, ClassType ):
    #     return called_type.__name__ + " constructor"
    # elif python_version < 3 and isinstance( called, InstanceType ):
    #     return called_type.__name__ + " instance"
    # else:
    #     return called_type.__name__ + " object"

    def makeNameAttributeLookup( node, attribute_name = "__name__" ):
        return ExpressionAttributeLookup(
            expression     = node,
            attribute_name = attribute_name,
            source_ref     = source_ref
        )

    functions_case = makeStatementsSequenceFromStatement(
        statement = (
            StatementReturn(
                expression = ExpressionOperationBinary(
                    operator   = "Add",
                    right      = ExpressionConstantRef(
                        constant      = "()",
                        source_ref    = source_ref,
                        user_provided = True
                    ),
                    left       = makeNameAttributeLookup(
                        makeCalledVariableRef()
                    ),
                    source_ref = source_ref

                ),
                source_ref = source_ref
            )
        )
    )

    no_branch = makeStatementsSequenceFromStatement(
        statement = StatementReturn(
            expression = ExpressionOperationBinary(
                operator   = "Add",
                right      = ExpressionConstantRef(
                    constant      = " object",
                    source_ref    = source_ref,
                    user_provided = True
                ),
                left       = makeNameAttributeLookup(
                    ExpressionBuiltinType1(
                        value      = makeCalledVariableRef(),
                        source_ref = source_ref
                    )
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
    )

    if python_version < 300:
        instance_case = makeStatementsSequenceFromStatement(
            statement = StatementReturn(
                expression = ExpressionOperationBinary(
                    operator   = "Add",
                    right      = ExpressionConstantRef(
                        constant      = " instance",
                        source_ref    = source_ref,
                        user_provided = True
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
            )
        )

        no_branch = makeStatementsSequenceFromStatement(
            statement = StatementConditional(
                condition  = ExpressionBuiltinIsinstance(
                    instance   = makeCalledVariableRef(),
                    cls        = ExpressionBuiltinAnonymousRef(
                        builtin_name = "instance",
                        source_ref   = source_ref
                    ),
                    source_ref = source_ref
                ),
                yes_branch = instance_case,
                no_branch  = no_branch,
                source_ref = source_ref
            )
        )

        class_case = makeStatementsSequenceFromStatement(
            statement = StatementReturn(
                expression = ExpressionOperationBinary(
                    operator   = "Add",
                    right      = ExpressionConstantRef(
                        constant      = " constructor",
                        source_ref    = source_ref,
                        user_provided = True
                    ),
                    left       = makeNameAttributeLookup(
                        makeCalledVariableRef(),
                    ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            )
        )

        no_branch = makeStatementsSequenceFromStatement(
            statement = StatementConditional(
                condition  = ExpressionBuiltinIsinstance(
                    instance   = makeCalledVariableRef(),
                    cls        = ExpressionBuiltinAnonymousRef(
                        builtin_name = "classobj",
                        source_ref   = source_ref
                    ),
                    source_ref = source_ref
                ),
                yes_branch = class_case,
                no_branch  = no_branch,
                source_ref = source_ref
            )
        )

    if python_version < 300:
        normal_cases = (
            "function", "builtin_function_or_method", "instancemethod"
        )
    else:
        normal_cases = (
            "function", "builtin_function_or_method"
        )

    statements = (
        StatementConditional(
            condition = ExpressionBuiltinIsinstance(
                instance   = makeCalledVariableRef(),
                cls        = ExpressionMakeTuple(
                    elements   = tuple(
                        ExpressionBuiltinAnonymousRef(
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

    result.setBody(
        StatementsSequence(
            statements = statements,
            source_ref = source_ref
        )
    )

    completeVariableClosures( result )

    return result

def _makeStarListArgumentToTupleStatement( called_variable_ref,
                                           star_list_target_variable_ref,
                                           star_list_variable_ref ):
    raise_statement = StatementRaiseException(
        exception_type  = ExpressionBuiltinMakeException(
            exception_name = "TypeError",
            args           = (
                ExpressionOperationBinary(
                    operator = "Mod",
                    left     =  ExpressionConstantRef(
                        constant      = """\
%s argument after * must be a sequence, not %s""",
                        source_ref    = source_ref,
                        user_provided = True
                    ),
                    right = ExpressionMakeTuple(
                        elements = (
                            ExpressionFunctionCall(
                                function   = ExpressionFunctionCreation(
                                    function_ref = ExpressionFunctionRef(
                                        function_body = getCallableNameDescBody(),
                                        source_ref    = source_ref
                                    ),
                                    defaults     = (),
                                    kw_defaults  = None,
                                    annotations  = None,
                                    source_ref   = source_ref
                                ),
                                values     = (
                                    called_variable_ref,
                                ),
                                source_ref = source_ref
                            ),
                            ExpressionAttributeLookup(
                                expression = ExpressionBuiltinType1(
                                    value      = star_list_variable_ref.makeCloneAt( source_ref ),
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

    handler_body = makeStatementsSequenceFromStatement(
        statement = raise_statement
    )

    return StatementConditional(
        condition  = ExpressionOperationNOT(
            operand = ExpressionBuiltinIsinstance(
                instance   = star_list_variable_ref.makeCloneAt( source_ref ),
                cls        = ExpressionBuiltinRef(
                    builtin_name = "tuple",
                    source_ref   = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        yes_branch = makeStatementsSequenceFromStatement(
            statement = makeTryExceptSingleHandlerNode(
                tried          =  makeStatementsSequenceFromStatement(
                    statement = StatementAssignmentVariable(
                        variable_ref = star_list_target_variable_ref.makeCloneAt( source_ref ),
                        source       = ExpressionBuiltinTuple(
                            value      = star_list_variable_ref.makeCloneAt( source_ref ),
                            source_ref = source_ref
                        ),
                        source_ref   = source_ref
                    )
                ),
                exception_name = "TypeError",
                handler_body   = handler_body,
                source_ref     = source_ref
            ),
        ),
        no_branch  = None,
        source_ref = source_ref
    )


def _makeStarDictArgumentToDictStatement( result, called_variable_ref,
                                          star_dict_target_variable_ref,
                                          star_dict_variable_ref ):
    raise_statement = StatementRaiseException(
        exception_type  = ExpressionBuiltinMakeException(
            exception_name = "TypeError",
            args           = (
                ExpressionOperationBinary(
                    operator = "Mod",
                    left     =  ExpressionConstantRef(
                        constant      = """\
%s argument after ** must be a mapping, not %s""",
                        source_ref    = source_ref,
                        user_provided = True
                    ),
                    right = ExpressionMakeTuple(
                        elements = (
                            ExpressionFunctionCall(
                                function   = ExpressionFunctionCreation(
                                    function_ref = ExpressionFunctionRef(
                                        function_body = getCallableNameDescBody(),
                                        source_ref    = source_ref
                                    ),
                                    defaults     = (),
                                    kw_defaults  = None,
                                    annotations  = None,
                                    source_ref   = source_ref
                                ),
                                values     = (
                                    called_variable_ref,
                                ),
                                source_ref = source_ref
                            ),
                            ExpressionAttributeLookup(
                                expression = ExpressionBuiltinType1(
                                    value      = star_dict_variable_ref.makeCloneAt( source_ref ),
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

    temp_scope = result.allocateTempScope( "mapping" )

    tmp_dict_variable = result.allocateTempVariable( temp_scope,  "dict" )
    tmp_iter_variable = result.allocateTempVariable( temp_scope,  "iter" )
    tmp_keys_variable = result.allocateTempVariable( temp_scope,  "keys" )
    tmp_key_variable = result.allocateTempVariable( temp_scope,  "key" )

    statements = (
        makeTryExceptSingleHandlerNode(
            tried          = makeStatementsSequenceFromStatement(
                statement = StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_key_variable.makeReference(
                            result
                        ),
                        source_ref = source_ref
                    ),
                    source     = ExpressionBuiltinNext1(
                        value      = ExpressionTempVariableRef(
                            variable   = tmp_iter_variable.makeReference(
                                result
                            ),
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                )
            ),
            exception_name = "StopIteration",
            handler_body   = makeStatementsSequenceFromStatement(
                statement = StatementBreakLoop(
                    source_ref = source_ref
                )
            ),
            source_ref     = source_ref
        ),
        StatementAssignmentSubscript(
            expression = ExpressionTempVariableRef(
                variable   = tmp_dict_variable.makeReference( result ),
                source_ref = source_ref
            ),
            subscript  = ExpressionTempVariableRef(
                variable   = tmp_key_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source     = ExpressionSubscriptLookup(
                expression = star_dict_variable_ref.makeCloneAt( source_ref ),
                subscript  = ExpressionTempVariableRef(
                    variable   = tmp_key_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    loop_body = StatementsSequence(
        statements = statements,
        source_ref = source_ref
    )

    statements = (
        # Initializing the temp variable outside of try/except, because code
        # generation does not yet detect that case properly. TODO: Can be
        # removed once code generation is apt enough.
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_keys_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source     = ExpressionConstantRef(
                constant      = None,
                source_ref    = source_ref,
                user_provided = True
            ),
            source_ref = source_ref
        ),
        makeTryExceptSingleHandlerNode(
            tried          = makeStatementsSequenceFromStatement(
                statement = StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_keys_variable.makeReference( result ),
                        source_ref = source_ref
                    ),
                    source     = ExpressionCallEmpty(
                        called = ExpressionAttributeLookup(
                            expression     = star_dict_variable_ref.makeCloneAt( source_ref ),
                            attribute_name = "keys",
                            source_ref     = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                ),
            ),
            exception_name = "AttributeError",
            handler_body   = makeStatementsSequenceFromStatement(
                statement = raise_statement
            ),
            source_ref     = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_iter_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source     = ExpressionBuiltinIter1(
                value      = ExpressionTempVariableRef(
                    variable   = tmp_keys_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_dict_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source     = ExpressionConstantRef(
                constant      = {},
                source_ref    = source_ref,
                user_provided = True
            ),
            source_ref = source_ref
        ),
        StatementLoop(
            body       = loop_body,
            source_ref = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = star_dict_target_variable_ref.makeCloneAt(
                source_ref = source_ref
            ),
            source     = ExpressionTempVariableRef(
                variable   = tmp_dict_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
    )

    mapping_case = StatementsSequence(
        statements = statements,
        source_ref = source_ref
    )

    return StatementConditional(
            condition  = ExpressionOperationNOT(
                operand    = ExpressionBuiltinIsinstance(
                    instance   = star_dict_variable_ref.makeCloneAt(
                        source_ref = source_ref
                    ),
                    cls        = ExpressionBuiltinRef(
                        builtin_name = "dict",
                        source_ref   = source_ref
                    ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            yes_branch = mapping_case,
            no_branch  = None,
            source_ref = source_ref
        )


def _makeStarDictArgumentMergeToKwStatement( result, called_variable_ref,
                                             kw_target_variable_ref,
                                             kw_variable_ref,
                                             star_dict_variable_ref ):
    # This is plain terribly complex, pylint: disable=R0914

    raise_statement = StatementRaiseException(
        exception_type  = ExpressionBuiltinMakeException(
            exception_name = "TypeError",
            args           = (
                ExpressionOperationBinary(
                    operator = "Mod",
                    left     =  ExpressionConstantRef(
                        constant      = """\
%s argument after ** must be a mapping, not %s""",
                        source_ref    = source_ref,
                        user_provided = True
                    ),
                    right = ExpressionMakeTuple(
                        elements = (
                            ExpressionFunctionCall(
                                function   = ExpressionFunctionCreation(
                                    function_ref = ExpressionFunctionRef(
                                        function_body = getCallableNameDescBody(),
                                        source_ref    = source_ref
                                    ),
                                    defaults     = (),
                                    kw_defaults  = None,
                                    annotations  = None,
                                    source_ref   = source_ref
                                ),
                                values     = (
                                    called_variable_ref.makeCloneAt(
                                        source_ref
                                    ),
                                ),
                                source_ref = source_ref
                            ),
                            ExpressionAttributeLookup(
                                expression = ExpressionBuiltinType1(
                                    value      = star_dict_variable_ref.makeCloneAt( source_ref ),
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

    temp_scope = result.allocateTempScope( "dict" )

    tmp_dict_variable = result.allocateTempVariable( temp_scope,  "dict" )
    tmp_keys_variable = result.allocateTempVariable( temp_scope,  "keys" )
    tmp_key_variable = result.allocateTempVariable( temp_scope,  "key_xxx" )
    tmp_iter_variable = result.allocateTempVariable( temp_scope,  "iter" )

    raise_duplicate = StatementRaiseException(
        exception_type  = ExpressionBuiltinMakeException(
            exception_name = "TypeError",
            args           = (
                ExpressionOperationBinary(
                    operator = "Mod",
                    left     =  ExpressionConstantRef(
                        constant      = """\
%s got multiple values for keyword argument '%s'""",
                        source_ref    = source_ref,
                        user_provided = True
                    ),
                    right = ExpressionMakeTuple(
                        elements = (
                            ExpressionFunctionCall(
                                function   = ExpressionFunctionCreation(
                                    function_ref = ExpressionFunctionRef(
                                        function_body = getCallableNameDescBody(
                                        ),
                                        source_ref    = source_ref
                                    ),
                                    defaults     = (),
                                    kw_defaults  = None,
                                    annotations  = None,
                                    source_ref   = source_ref
                                ),
                                values     = (
                                    called_variable_ref.makeCloneAt(
                                        source_ref
                                    ),
                                ),
                                source_ref = source_ref
                            ),
                            ExpressionTempVariableRef(
                                variable   = tmp_key_variable.makeReference(
                                    result
                                ),
                                source_ref = source_ref
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

    statements = (
        makeTryExceptSingleHandlerNode(
            tried          = makeStatementsSequenceFromStatement(
                statement = StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_key_variable.makeReference( result ),
                        source_ref = source_ref
                    ),
                    source     = ExpressionBuiltinNext1(
                        value      = ExpressionTempVariableRef(
                            variable   = tmp_iter_variable.makeReference(
                                result
                            ),
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                )
            ),
            exception_name = "StopIteration",
            handler_body   = makeStatementsSequenceFromStatement(
                statement = StatementBreakLoop(
                    source_ref = source_ref
                )
            ),
            source_ref     = source_ref
        ),
        StatementConditional(
            condition = ExpressionComparison(
                comparator = "In",
                left       = ExpressionTempVariableRef(
                    variable   = tmp_key_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                right      = kw_variable_ref.makeCloneAt( source_ref ),
                source_ref = source_ref
            ),
            yes_branch = makeStatementsSequenceFromStatement(
                statement = raise_duplicate
            ),
            no_branch  = None,
            source_ref = source_ref
        ),
        StatementAssignmentSubscript(
            expression = kw_variable_ref.makeCloneAt( source_ref ),
            subscript  = ExpressionTempVariableRef(
                variable   = tmp_key_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source     = ExpressionSubscriptLookup(
                expression = star_dict_variable_ref.makeCloneAt( source_ref ),
                subscript  = ExpressionTempVariableRef(
                    variable   = tmp_key_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    mapping_loop_body = StatementsSequence(
        statements = statements,
        source_ref = source_ref
    )

    statements = (
        # Initializing the temp variable outside of try/except, because code
        # generation does not yet detect that case properly. TODO: Can be
        # removed once code generation is apt enough.
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_keys_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source     = ExpressionConstantRef(
                constant      = None,
                source_ref    = source_ref,
                user_provided = True
            ),
            source_ref = source_ref
        ),
        makeTryExceptSingleHandlerNode(
            tried          = makeStatementsSequenceFromStatement(
                statement = StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_keys_variable.makeReference( result ),
                        source_ref = source_ref
                    ),
                    source     = ExpressionCallEmpty(
                        called = ExpressionAttributeLookup(
                            expression     = star_dict_variable_ref.makeCloneAt(
                                source_ref
                            ),
                            attribute_name = "keys",
                            source_ref     = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                )
            ),
            exception_name = "AttributeError",
            handler_body   = makeStatementsSequenceFromStatement(
                statement = raise_statement
            ),
            source_ref = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_iter_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source     = ExpressionBuiltinIter1(
                value      = ExpressionTempVariableRef(
                    variable   = tmp_keys_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_dict_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source     = ExpressionConstantRef(
                constant      = {},
                source_ref    = source_ref,
                user_provided = True
            ),
            source_ref = source_ref
        ),
        StatementLoop(
            body       = mapping_loop_body,
            source_ref = source_ref
        ),
    )

    mapping_case = StatementsSequence(
        statements = statements,
        source_ref = source_ref
    )

    temp_scope = result.allocateTempScope( "dict" )

    tmp_iter_variable = result.allocateTempVariable( temp_scope,  "iter" )
    tmp_item_variable = result.allocateTempVariable( temp_scope,  "item" )
    tmp_key_variable = result.allocateTempVariable( temp_scope,  "key" )

    # TODO: Duplication from above, just so the other temp is used.
    raise_duplicate = StatementRaiseException(
        exception_type  = ExpressionBuiltinMakeException(
            exception_name = "TypeError",
            args           = (
                ExpressionOperationBinary(
                    operator = "Mod",
                    left     =  ExpressionConstantRef(
                        constant      = """\
%s got multiple values for keyword argument '%s'""",
                        source_ref    = source_ref,
                        user_provided = True
                    ),
                    right = ExpressionMakeTuple(
                        elements = (
                            ExpressionFunctionCall(
                                function   = ExpressionFunctionCreation(
                                    function_ref = ExpressionFunctionRef(
                                        function_body = getCallableNameDescBody(
                                        ),
                                        source_ref    = source_ref
                                    ),
                                    defaults     = (),
                                    kw_defaults  = None,
                                    annotations  = None,
                                    source_ref   = source_ref
                                ),
                                values     = (
                                    called_variable_ref.makeCloneAt(
                                        source_ref
                                    ),
                                ),
                                source_ref = source_ref
                            ),
                            ExpressionTempVariableRef(
                                variable   = tmp_key_variable.makeReference(
                                    result
                                ),
                                source_ref = source_ref
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

    statements = (
        makeTryExceptSingleHandlerNode(
            tried          = makeStatementsSequenceFromStatement(
                statement = StatementAssignmentVariable(
                    variable_ref = ExpressionTargetTempVariableRef(
                        variable   = tmp_item_variable.makeReference( result ),
                        source_ref = source_ref
                    ),
                    source     = ExpressionBuiltinNext1(
                        value      = ExpressionTempVariableRef(
                            variable   = tmp_iter_variable.makeReference(
                                result
                            ),
                            source_ref = source_ref
                        ),
                        source_ref = source_ref
                    ),
                    source_ref = source_ref
                )
            ),
            exception_name = "StopIteration",
            handler_body   = makeStatementsSequenceFromStatement(
                statement = StatementBreakLoop( source_ref )
            ),
            source_ref     = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_key_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source     = ExpressionSubscriptLookup(
                expression = ExpressionTempVariableRef(
                    variable   = tmp_item_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                subscript  = ExpressionConstantRef(
                    constant      = 0,
                    source_ref    = source_ref,
                    user_provided = True
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        StatementConditional(
            condition = ExpressionComparison(
                comparator = "In",
                left       = ExpressionTempVariableRef(
                    variable   = tmp_key_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                right      = kw_variable_ref.makeCloneAt( source_ref ),
                source_ref = source_ref
            ),
            yes_branch = makeStatementsSequenceFromStatement(
                statement = raise_duplicate,
            ),
            no_branch  = None,
            source_ref = source_ref
        ),
        StatementAssignmentSubscript(
            expression = kw_variable_ref.makeCloneAt( source_ref ),
            subscript  = ExpressionTempVariableRef(
                variable   = tmp_key_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source     = ExpressionSubscriptLookup(
                expression = ExpressionTempVariableRef(
                    variable   = tmp_item_variable.makeReference( result ),
                    source_ref = source_ref
                ),
                subscript  = ExpressionConstantRef(
                    constant      = 1,
                    source_ref    = source_ref,
                    user_provided = True
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    dict_loop_body = StatementsSequence(
        statements = statements,
        source_ref = source_ref
    )

    statements = (
        StatementAssignmentVariable(
            variable_ref = kw_target_variable_ref.makeCloneAt( source_ref ),
            source       = ExpressionBuiltinDict(
                pos_arg    = kw_variable_ref.makeCloneAt( source_ref ),
                pairs      = (),
                source_ref = source_ref
            ),
            source_ref   = source_ref
        ),
        StatementAssignmentVariable(
            variable_ref = ExpressionTargetTempVariableRef(
                variable   = tmp_iter_variable.makeReference( result ),
                source_ref = source_ref
            ),
            source       = ExpressionBuiltinIter1(
                value = ExpressionCallEmpty(
                    called = ExpressionAttributeLookup(
                        expression     = star_dict_variable_ref.makeCloneAt(
                            source_ref
                        ),
                        attribute_name = "iteritems"
                                           if python_version < 300 else
                                         "items",
                        source_ref     = source_ref
                    ),
                    source_ref     = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref   = source_ref
        ),
        StatementLoop(
            body       = dict_loop_body,
            source_ref = source_ref
        ),
    )

    dict_case = StatementsSequence(
        statements = statements,
        source_ref = source_ref
    )

    statements = (
        StatementConditional(
            condition  = star_dict_variable_ref.makeCloneAt( source_ref ),
            yes_branch = dict_case,
            no_branch  = None,
            source_ref = source_ref
        ),
    )

    dict_case = StatementsSequence(
        statements = statements,
        source_ref = source_ref
    )

    return StatementConditional(
        condition  = ExpressionOperationNOT(
            operand    = ExpressionBuiltinIsinstance(
                instance   = star_dict_variable_ref.makeCloneAt( source_ref ),
                cls        = ExpressionBuiltinRef(
                    builtin_name = "dict",
                    source_ref   = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        ),
        yes_branch = mapping_case,
        no_branch  = dict_case,
        source_ref = source_ref
    )


@once_decorator
def getFunctionCallHelperStarList():
    helper_name = "complex_call_helper_star_list"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
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

    # Equivalent of:
    #
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call.
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

    statements = (
        _makeStarListArgumentToTupleStatement(
            called_variable_ref           = makeCalledVariableRef(),
            star_list_variable_ref        = makeStarListArgVariableRef(
                assign = False
            ),
            star_list_target_variable_ref = makeStarListArgVariableRef(
                assign = True
            )
        ),
        StatementReturn(
            expression = ExpressionCallNoKeywords(
                called     = makeCalledVariableRef(),
                args       = makeStarListArgVariableRef( assign = False ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        makePseudoFrame(
            parameters = result.getParameters(),
            statements = statements
        )
    )

    completeVariableClosures( result )

    return result

@once_decorator
def getFunctionCallHelperKeywordsStarList():
    helper_name = "complex_call_helper_keywords_star_list"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = ( "called", "kw", "star_arg_list" ),
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
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call.
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

    statements = (
        _makeStarListArgumentToTupleStatement(
            called_variable_ref           = makeCalledVariableRef(),
            star_list_variable_ref        = makeStarListArgVariableRef(
                assign = False
            ),
            star_list_target_variable_ref = makeStarListArgVariableRef(
                assign = True
            )
        ),
        StatementReturn(
            expression = ExpressionCall(
                called     = makeCalledVariableRef(),
                args       = makeStarListArgVariableRef( assign = False ),
                kw         = makeKwVariableRef( assign = False),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        makePseudoFrame(
            parameters = result.getParameters(),
            statements = statements
        )
    )

    completeVariableClosures( result )

    return result

@once_decorator
def getFunctionCallHelperPosStarList():
    helper_name = "complex_call_helper_pos_star_list"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = ( "called", "args", "star_arg_list" ),
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
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call.
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

    statements = (
        _makeStarListArgumentToTupleStatement(
            called_variable_ref           = makeCalledVariableRef(),
            star_list_variable_ref        = makeStarListArgVariableRef(
                assign = False
            ),
            star_list_target_variable_ref = makeStarListArgVariableRef(
                assign = True
            )
        ),
        StatementReturn(
            expression = ExpressionCallNoKeywords(
                called     = makeCalledVariableRef(),
                args       = ExpressionOperationBinary(
                    operator   = "Add",
                    left       = makeArgsVariableRef(),
                    right      = makeStarListArgVariableRef( assign = False ),
                    source_ref = source_ref
                ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        makePseudoFrame(
            parameters = result.getParameters(),
            statements = statements
        )
    )

    completeVariableClosures( result )

    return result

@once_decorator
def getFunctionCallHelperPosKeywordsStarList():
    helper_name = "complex_call_helper_pos_keywords_star_list"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = ( "called", "args", "kw", "star_arg_list" ),
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
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call.
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

    statements = (
        _makeStarListArgumentToTupleStatement(
            called_variable_ref           = makeCalledVariableRef(),
            star_list_variable_ref        = makeStarListArgVariableRef(
                assign = False
            ),
            star_list_target_variable_ref = makeStarListArgVariableRef(
                assign = True
            )
        ),
        StatementReturn(
            expression = ExpressionCall(
                called     = makeCalledVariableRef(),
                args       = ExpressionOperationBinary(
                    operator   = "Add",
                    left       = makeArgsVariableRef(),
                    right      = makeStarListArgVariableRef( assign = False ),
                    source_ref = source_ref
                ),
                kw         = makeKwVariableRef( assign = False ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        makePseudoFrame(
            parameters = result.getParameters(),
            statements = statements
        )
    )

    completeVariableClosures( result )

    return result

@once_decorator
def getFunctionCallHelperStarDict():
    helper_name = "complex_call_helper_star_dict"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = ( "called", "star_arg_dict" ),
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
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call.
    #
    # if not isinstance( star_arg_dict, dict ):
    #     try:
    #         tmp_keys =  star_arg_dict.keys()
    #     except AttributeError:
    #         raise TypeError, ""%s argument after ** must be a mapping, not %s" % (
    #             get_callable_name_desc( function ),
    #             type( star_arg_dict ).__name__
    #         )
    #
    #     tmp_iter = iter( keys )
    #     tmp_dict = {}
    #
    #     while 1:
    #         try:
    #             tmp_key = tmp_iter.next()
    #         except StopIteration:
    #             break
    #
    #         tmp_dict[ tmp_key ] = star_dict_arg[ tmp_key )
    #
    #     star_arg_dict = new
    #
    # return called( **star_arg_dict )

    statements = (
        _makeStarDictArgumentToDictStatement(
            result                        = result,
            called_variable_ref           = makeCalledVariableRef(),
            star_dict_variable_ref        = makeStarDictArgVariableRef(
                assign = False
            ),
            star_dict_target_variable_ref = makeStarDictArgVariableRef(
                assign = True
            )
        ),
        StatementReturn(
            expression = ExpressionCallKeywordsOnly(
                called     = makeCalledVariableRef(),
                kw         = makeStarDictArgVariableRef( assign = False ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        makePseudoFrame(
            parameters = result.getParameters(),
            statements = statements
        )
    )

    completeVariableClosures( result )

    return result

@once_decorator
def getFunctionCallHelperPosStarDict():
    helper_name = "complex_call_helper_pos_star_dict"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = ( "called", "args", "star_arg_dict" ),
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
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call.
    #
    # if not isinstance( star_arg_dict, dict ):
    #     try:
    #         tmp_keys =  star_arg_dict.keys()
    #     except AttributeError:
    #         raise TypeError, ""%s argument after ** must be a mapping, not %s" % (
    #             get_callable_name_desc( function ),
    #             type( star_arg_dict ).__name__
    #         )
    #
    #     tmp_iter = iter( keys )
    #     tmp_dict = {}
    #
    #     while 1:
    #         try:
    #             tmp_key = tmp_iter.next()
    #         except StopIteration:
    #             break
    #
    #         tmp_dict[ tmp_key ] = star_dict_arg[ tmp_key )
    #
    #     star_arg_dict = new
    #
    # return called( args, **star_arg_dict )

    statements = (
        _makeStarDictArgumentToDictStatement(
            result                        = result,
            called_variable_ref           = makeCalledVariableRef(),
            star_dict_variable_ref        = makeStarDictArgVariableRef(
                assign = False
            ),
            star_dict_target_variable_ref = makeStarDictArgVariableRef(
                assign = True
            )
        ),
        StatementReturn(
            expression = ExpressionCall(
                called     = makeCalledVariableRef(),
                args       = makeArgsVariableRef(),
                kw         = makeStarDictArgVariableRef( assign = False ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        makePseudoFrame(
            parameters = result.getParameters(),
            statements = statements
        )
    )

    completeVariableClosures( result )

    return result

@once_decorator
def getFunctionCallHelperKeywordsStarDict():
    helper_name = "complex_call_helper_keywords_star_dict"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = ( "called", "kw", "star_arg_dict" ),
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
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call. One goal is to avoid copying "kw" unless really
    # necessary, and to take the slow route only for non-dictionaries.
    #
    # if not isinstance( star_arg_dict, dict ):
    #     try:
    #         tmp_keys =  star_arg_dict.keys()
    #     except AttributeError:
    #         raise TypeError, ""%s argument after ** must be a mapping, not %s" % (
    #             get_callable_name_desc( function ),
    #             type( star_arg_dict ).__name__
    #         )
    #
    #     if keys:
    #         kw = dict( kw )
    #
    #         tmp_iter = iter( keys )
    #         tmp_dict = {}
    #
    #         while 1:
    #             try:
    #                 tmp_key = tmp_iter.next()
    #             except StopIteration:
    #                  break
    #
    #             if tmp_key in kw:
    #                 raise TypeError, "%s got multiple values for keyword argument '%s'" % (
    #                     get_callable_name_desc( function ),
    #                     tmp_key
    #                 )
    #
    #             kw[ tmp_key ] = star_dict_arg[ tmp_key )
    #
    # elif star_arg_dict:
    #    tmp_iter = star_arg_dict.iteritems()
    #
    #    kw = dict( kw )
    #    while 1:
    #        try:
    #            tmp_key, tmp_value = tmp_iter.next()
    #        except StopIteration:
    #            break
    #
    #        if tmp_key in kw:
    #            raise TypeError, "%s got multiple values for keyword argument '%s'" % (
    #                 get_callable_name_desc( function ),
    #                 tmp_key
    #            )
    #
    #        kw[ tmp_key ] = tmp_value
    #
    # return called( **kw  )

    statements = (
        _makeStarDictArgumentMergeToKwStatement(
            result                        = result,
            called_variable_ref           = makeCalledVariableRef(),
            kw_variable_ref               = makeKwVariableRef( assign = False ),
            kw_target_variable_ref        = makeKwVariableRef( assign = True ),
            star_dict_variable_ref        = makeStarDictArgVariableRef(
                assign = False
            )
        ),
        StatementReturn(
            expression = ExpressionCallKeywordsOnly(
                called     = makeCalledVariableRef(),
                kw         = makeKwVariableRef( assign = False ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        makePseudoFrame(
            parameters = result.getParameters(),
            statements = statements
        )
    )

    completeVariableClosures( result )

    return result

@once_decorator
def getFunctionCallHelperPosKeywordsStarDict():
    helper_name = "complex_call_helper_pos_keywords_star_dict"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = ( "called", "args", "kw", "star_arg_dict" ),
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
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call. One goal is to avoid copying "kw" unless really
    # necessary, and to take the slow route only for non-dictionaries.
    #
    # if not isinstance( star_arg_dict, dict ):
    #     try:
    #         tmp_keys =  star_arg_dict.keys()
    #     except AttributeError:
    #         raise TypeError, ""%s argument after ** must be a mapping, not %s" % (
    #             get_callable_name_desc( function ),
    #             type( star_arg_dict ).__name__
    #         )
    #
    #     if keys:
    #         kw = dict( kw )
    #
    #         tmp_iter = iter( keys )
    #         tmp_dict = {}
    #
    #         while 1:
    #             try:
    #                 tmp_key = tmp_iter.next()
    #             except StopIteration:
    #                  break
    #
    #             if tmp_key in kw:
    #                 raise TypeError, "%s got multiple values for keyword argument '%s'" % (
    #                     get_callable_name_desc( function ),
    #                     tmp_key
    #                 )
    #
    #             kw[ tmp_key ] = star_dict_arg[ tmp_key )
    #
    # elif star_arg_dict:
    #    tmp_iter = star_arg_dict.iteritems()
    #
    #    kw = dict( kw )
    #    while 1:
    #        try:
    #            tmp_key, tmp_value = tmp_iter.next()
    #        except StopIteration:
    #            break
    #
    #        if tmp_key in kw:
    #            raise TypeError, "%s got multiple values for keyword argument '%s'" % (
    #                 get_callable_name_desc( function ),
    #                 tmp_key
    #            )
    #
    #        kw[ tmp_key ] = tmp_value
    #
    # return called( **kw  )

    statements = (
        _makeStarDictArgumentMergeToKwStatement(
            result                        = result,
            called_variable_ref           = makeCalledVariableRef(),
            kw_variable_ref               = makeKwVariableRef( assign = False ),
            kw_target_variable_ref        = makeKwVariableRef( assign = True ),
            star_dict_variable_ref        = makeStarDictArgVariableRef(
                assign = False
            )
        ),
        StatementReturn(
            expression = ExpressionCall(
                called     = makeCalledVariableRef(),
                args       = makeArgsVariableRef(),
                kw         = makeKwVariableRef( assign = False ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        makePseudoFrame(
            parameters = result.getParameters(),
            statements = statements
        )
    )

    completeVariableClosures( result )

    return result

@once_decorator
def getFunctionCallHelperStarListStarDict():
    helper_name = "complex_call_helper_star_list_star_dict"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = ( "called", "star_arg_list", "star_arg_dict" ),
            list_star_arg = None,
            dict_star_arg = None,
            default_count = 0,
            kw_only_args  = ()
        ),
        source_ref = source_ref,
        is_class   = False
    )

    statements = (
        _makeStarDictArgumentToDictStatement(
            result                        = result,
            called_variable_ref           = makeCalledVariableRef(),
            star_dict_variable_ref        = makeStarDictArgVariableRef(
                assign = False
            ),
            star_dict_target_variable_ref = makeStarDictArgVariableRef(
                assign = True
            )
        ),
        _makeStarListArgumentToTupleStatement(
            called_variable_ref           = makeCalledVariableRef(),
            star_list_variable_ref        = makeStarListArgVariableRef(
                assign = False
            ),
            star_list_target_variable_ref = makeStarListArgVariableRef(
                assign = True
            )
        ),
        StatementReturn(
            expression = ExpressionCall(
                called     = makeCalledVariableRef(),
                args       = makeStarListArgVariableRef( assign = False ),
                kw         = makeStarDictArgVariableRef( assign = False ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        makePseudoFrame(
            parameters = result.getParameters(),
            statements = statements
        )
    )

    completeVariableClosures( result )

    return result

@once_decorator
def getFunctionCallHelperPosStarListStarDict():
    helper_name = "complex_call_helper_pos_star_list_star_dict"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = (
                "called", "args", "star_arg_list", "star_arg_dict"
            ),
            list_star_arg = None,
            dict_star_arg = None,
            default_count = 0,
            kw_only_args  = ()
        ),
        source_ref = source_ref,
        is_class   = False
    )

    statements = (
        _makeStarDictArgumentToDictStatement(
            result                        = result,
            called_variable_ref           = makeCalledVariableRef(),
            star_dict_variable_ref        = makeStarDictArgVariableRef(
                assign = False
            ),
            star_dict_target_variable_ref = makeStarDictArgVariableRef(
                assign = True
            )
        ),
        _makeStarListArgumentToTupleStatement(
            called_variable_ref           = makeCalledVariableRef(),
            star_list_variable_ref        = makeStarListArgVariableRef(
                assign = False
            ),
            star_list_target_variable_ref = makeStarListArgVariableRef(
                assign = True
            )
        ),
        StatementReturn(
            expression = ExpressionCall(
                called     = makeCalledVariableRef(),
                args       = ExpressionOperationBinary(
                    operator   = "Add",
                    left       = makeArgsVariableRef(),
                    right      = makeStarListArgVariableRef( assign = False ),
                    source_ref = source_ref
                ),
                kw         = makeStarDictArgVariableRef( assign = False ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        makePseudoFrame(
            parameters = result.getParameters(),
            statements = statements
        )
    )

    completeVariableClosures( result )

    return result

@once_decorator
def getFunctionCallHelperKeywordsStarListStarDict():
    helper_name = "complex_call_helper_keywords_star_list_star_dict"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = (
                "called", "kw", "star_arg_list", "star_arg_dict"
            ),
            list_star_arg = None,
            dict_star_arg = None,
            default_count = 0,
            kw_only_args  = ()
        ),
        source_ref = source_ref,
        is_class   = False
    )

    statements = (
        _makeStarDictArgumentMergeToKwStatement(
            result                        = result,
            called_variable_ref           = makeCalledVariableRef(),
            kw_variable_ref               = makeKwVariableRef( assign = False ),
            kw_target_variable_ref        = makeKwVariableRef( assign = True ),
            star_dict_variable_ref        = makeStarDictArgVariableRef(
                assign = False
            )
        ),
        _makeStarListArgumentToTupleStatement(
            called_variable_ref           = makeCalledVariableRef(),
            star_list_variable_ref        = makeStarListArgVariableRef(
                assign = False
            ),
            star_list_target_variable_ref = makeStarListArgVariableRef(
                assign = True
            )
        ),
        StatementReturn(
            expression = ExpressionCall(
                called     = makeCalledVariableRef(),
                args       = makeStarListArgVariableRef( assign = False ),
                kw         = makeKwVariableRef( assign = False ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        makePseudoFrame(
            parameters = result.getParameters(),
            statements = statements
        )
    )

    completeVariableClosures( result )

    return result

@once_decorator
def getFunctionCallHelperPosKeywordsStarListStarDict():
    helper_name = "complex_call_helper_pos_keywords_star_list_star_dict"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = ExpressionFunctionBody(
        provider   = getInternalModule(),
        name       = helper_name,
        doc        = None,
        parameters = ParameterSpec(
            name          = helper_name,
            normal_args   = (
                "called", "args", "kw", "star_arg_list", "star_arg_dict"
            ),
            list_star_arg = None,
            dict_star_arg = None,
            default_count = 0,
            kw_only_args  = ()
        ),
        source_ref = source_ref,
        is_class   = False
    )

    statements = (
        _makeStarDictArgumentMergeToKwStatement(
            result                        = result,
            called_variable_ref           = makeCalledVariableRef(),
            kw_variable_ref               = makeKwVariableRef( assign = False ),
            kw_target_variable_ref        = makeKwVariableRef( assign = True ),
            star_dict_variable_ref        = makeStarDictArgVariableRef(
                assign = False
            )
        ),
        _makeStarListArgumentToTupleStatement(
            called_variable_ref           = makeCalledVariableRef(),
            star_list_variable_ref        = makeStarListArgVariableRef(
                assign = False
            ),
            star_list_target_variable_ref = makeStarListArgVariableRef(
                assign = True
            )
        ),
        StatementReturn(
            expression = ExpressionCall(
                called     = makeCalledVariableRef(),
                args       = ExpressionOperationBinary(
                    operator   = "Add",
                    left       = makeArgsVariableRef(),
                    right      = makeStarListArgVariableRef( assign = False ),
                    source_ref = source_ref
                ),
                kw         = makeKwVariableRef( assign = False ),
                source_ref = source_ref
            ),
            source_ref = source_ref
        )
    )

    result.setBody(
        makePseudoFrame(
            parameters = result.getParameters(),
            statements = statements
        )
    )

    completeVariableClosures( result )

    return result
