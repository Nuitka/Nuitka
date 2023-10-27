#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.nodes.AttributeNodes import (
    ExpressionAttributeCheck,
    makeExpressionAttributeLookup,
)
from nuitka.nodes.BuiltinDictNodes import ExpressionBuiltinDict
from nuitka.nodes.BuiltinIteratorNodes import ExpressionBuiltinIter1
from nuitka.nodes.BuiltinNextNodes import ExpressionBuiltinNext1
from nuitka.nodes.BuiltinRefNodes import (
    ExpressionBuiltinAnonymousRef,
    makeExpressionBuiltinTypeRef,
)
from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinTuple
from nuitka.nodes.CallNodes import makeExpressionCall
from nuitka.nodes.ComparisonNodes import (
    ExpressionComparisonIn,
    ExpressionComparisonIsNot,
)
from nuitka.nodes.ConditionalNodes import (
    ExpressionConditionalOr,
    makeStatementConditional,
)
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import makeExpressionMakeTuple
from nuitka.nodes.DictionaryNodes import (
    ExpressionDictOperationIteritems,
    StatementDictOperationSet,
    StatementDictOperationSetKeyValue,
)
from nuitka.nodes.ExceptionNodes import (
    ExpressionBuiltinMakeException,
    StatementRaiseException,
)
from nuitka.nodes.FunctionAttributeNodes import ExpressionFunctionErrorStr
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionRef,
    makeExpressionFunctionCall,
    makeExpressionFunctionCreation,
)
from nuitka.nodes.LoopNodes import StatementLoop, StatementLoopBreak
from nuitka.nodes.OperatorNodes import makeBinaryOperationNode
from nuitka.nodes.ReturnNodes import StatementReturn
from nuitka.nodes.SubscriptNodes import (
    ExpressionSubscriptLookup,
    StatementAssignmentSubscript,
)
from nuitka.nodes.TypeNodes import (
    ExpressionBuiltinIsinstance,
    ExpressionBuiltinType1,
)
from nuitka.nodes.VariableAssignNodes import makeStatementAssignmentVariable
from nuitka.nodes.VariableRefNodes import (
    ExpressionTempVariableRef,
    ExpressionVariableRef,
)
from nuitka.nodes.VariableReleaseNodes import makeStatementsReleaseVariables
from nuitka.PythonVersions import (
    getComplexCallSequenceErrorTemplate,
    python_version,
)
from nuitka.specs.ParameterSpecs import ParameterSpec

from .InternalModule import (
    internal_source_ref,
    makeInternalHelperFunctionBody,
    once_decorator,
)
from .ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode
from .ReformulationTryFinallyStatements import makeTryFinallyStatement
from .TreeHelpers import (
    makeCallNode,
    makeStatementsSequenceFromStatement,
    makeStatementsSequenceFromStatements,
)

# TODO: Consider using ExpressionOutlineNodes for at least some of these
# or their own helpers.


def orderArgs(*args):
    if python_version >= 0x350:

        def weight(arg):
            result = args.index(arg)

            if arg == "kw":
                result += 1.5
            elif arg == "star_arg_list":
                result -= 1.5

            return result

        return tuple(sorted(args, key=weight))

    return args


def _makeNameAttributeLookup(node, attribute_name="__name__"):
    return makeExpressionAttributeLookup(
        expression=node, attribute_name=attribute_name, source_ref=internal_source_ref
    )


@once_decorator
def getCallableNameDescBody():
    helper_name = "get_callable_name_desc"

    # Equivalent of:
    #
    # Note: The "called_type" is a temporary variable.
    #
    # called_type = type(BuiltinFunctionType)
    #
    # if isinstance(called, (FunctionType, MethodType, BuiltinFunctionType)):
    #     return called.__name__
    # elif python_version < 0x3 and isinstance(called, ClassType):
    #     return called_type.__name__ + " constructor"
    # elif python_version < 0x3 and isinstance(called, InstanceType):
    #     return called_type.__name__ + " instance"
    # else:
    #     return called_type.__name__ + " object"

    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=("called",),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")

    if python_version < 0x390:
        function_name = makeBinaryOperationNode(
            operator="Add",
            left=_makeNameAttributeLookup(
                node=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                attribute_name="__name__",
            ),
            right=makeConstantRefNode(
                constant="()",
                source_ref=internal_source_ref,
                user_provided=True,
            ),
            source_ref=internal_source_ref,
        )
    else:
        # TODO: Make it usable for pre-Python 3.9 too.
        function_name = ExpressionFunctionErrorStr(
            value=ExpressionVariableRef(
                variable=called_variable, source_ref=internal_source_ref
            ),
            source_ref=internal_source_ref,
        )

    functions_case = makeStatementsSequenceFromStatement(
        statement=(
            StatementReturn(
                expression=function_name,
                source_ref=internal_source_ref,
            )
        )
    )

    if python_version >= 0x390:
        result.setChildBody(functions_case)

        return result

    no_branch = StatementReturn(
        expression=makeBinaryOperationNode(
            operator="Add",
            right=makeConstantRefNode(
                constant=" object", source_ref=internal_source_ref, user_provided=True
            ),
            left=_makeNameAttributeLookup(
                ExpressionBuiltinType1(
                    value=ExpressionVariableRef(
                        variable=called_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                )
            ),
            source_ref=internal_source_ref,
        ),
        source_ref=internal_source_ref,
    )

    if python_version < 0x300:
        instance_case = StatementReturn(
            expression=makeBinaryOperationNode(
                operator="Add",
                right=makeConstantRefNode(
                    constant=" instance",
                    source_ref=internal_source_ref,
                    user_provided=True,
                ),
                left=_makeNameAttributeLookup(
                    _makeNameAttributeLookup(
                        ExpressionVariableRef(
                            variable=called_variable, source_ref=internal_source_ref
                        ),
                        attribute_name="__class__",
                    )
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        )

        no_branch = makeStatementConditional(
            condition=ExpressionBuiltinIsinstance(
                instance=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                classes=ExpressionBuiltinAnonymousRef(
                    builtin_name="instance", source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            yes_branch=instance_case,
            no_branch=no_branch,
            source_ref=internal_source_ref,
        )

        class_case = StatementReturn(
            expression=makeBinaryOperationNode(
                operator="Add",
                right=makeConstantRefNode(
                    constant=" constructor",
                    source_ref=internal_source_ref,
                    user_provided=True,
                ),
                left=_makeNameAttributeLookup(
                    ExpressionVariableRef(
                        variable=called_variable, source_ref=internal_source_ref
                    )
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        )

        no_branch = makeStatementConditional(
            condition=ExpressionBuiltinIsinstance(
                instance=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                classes=ExpressionBuiltinAnonymousRef(
                    builtin_name="classobj", source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            yes_branch=class_case,
            no_branch=no_branch,
            source_ref=internal_source_ref,
        )

    if python_version < 0x300:
        normal_cases = ("function", "builtin_function_or_method", "instancemethod")
    else:
        normal_cases = ("function", "builtin_function_or_method")

    result.setChildBody(
        makeStatementsSequenceFromStatement(
            statement=makeStatementConditional(
                condition=ExpressionBuiltinIsinstance(
                    instance=ExpressionVariableRef(
                        variable=called_variable, source_ref=internal_source_ref
                    ),
                    classes=makeExpressionMakeTuple(
                        elements=tuple(
                            ExpressionBuiltinAnonymousRef(
                                builtin_name=builtin_name,
                                source_ref=internal_source_ref,
                            )
                            for builtin_name in normal_cases
                        ),
                        source_ref=internal_source_ref,
                    ),
                    source_ref=internal_source_ref,
                ),
                yes_branch=functions_case,
                no_branch=no_branch,
                source_ref=internal_source_ref,
            )
        )
    )

    return result


def makeStarListArgumentErrorRaise(called_variable, star_list_variable):
    return StatementRaiseException(
        exception_type=ExpressionBuiltinMakeException(
            exception_name="TypeError",
            args=(
                makeBinaryOperationNode(
                    operator="Mod",
                    left=makeConstantRefNode(
                        constant=getComplexCallSequenceErrorTemplate(),
                        source_ref=internal_source_ref,
                        user_provided=True,
                    ),
                    right=makeExpressionMakeTuple(
                        elements=(
                            makeExpressionFunctionCall(
                                function=makeExpressionFunctionCreation(
                                    function_ref=ExpressionFunctionRef(
                                        function_body=getCallableNameDescBody(),
                                        source_ref=internal_source_ref,
                                    ),
                                    defaults=(),
                                    kw_defaults=None,
                                    annotations=None,
                                    source_ref=internal_source_ref,
                                ),
                                values=(
                                    ExpressionVariableRef(
                                        variable=called_variable,
                                        source_ref=internal_source_ref,
                                    ),
                                ),
                                source_ref=internal_source_ref,
                            ),
                            _makeNameAttributeLookup(
                                ExpressionBuiltinType1(
                                    value=ExpressionVariableRef(
                                        variable=star_list_variable,
                                        source_ref=internal_source_ref,
                                    ),
                                    source_ref=internal_source_ref,
                                )
                            ),
                        ),
                        source_ref=internal_source_ref,
                    ),
                    source_ref=internal_source_ref,
                ),
            ),
            source_ref=internal_source_ref,
        ),
        exception_value=None,
        exception_trace=None,
        exception_cause=None,
        source_ref=internal_source_ref,
    )


def _makeStarListArgumentToTupleStatement(called_variable, star_list_variable):
    if python_version >= 0x350:
        non_tuple_code = makeStatementConditional(
            condition=ExpressionConditionalOr(
                left=ExpressionAttributeCheck(
                    expression=ExpressionVariableRef(
                        variable=star_list_variable, source_ref=internal_source_ref
                    ),
                    attribute_name="__iter__",
                    source_ref=internal_source_ref,
                ),
                right=ExpressionAttributeCheck(
                    expression=ExpressionVariableRef(
                        variable=star_list_variable, source_ref=internal_source_ref
                    ),
                    attribute_name="__getitem__",
                    source_ref=internal_source_ref,
                ),
                source_ref=internal_source_ref,
            ),
            yes_branch=makeStatementAssignmentVariable(
                variable=star_list_variable,
                source=ExpressionBuiltinTuple(
                    value=ExpressionVariableRef(
                        variable=star_list_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                source_ref=internal_source_ref,
            ),
            no_branch=makeStarListArgumentErrorRaise(
                called_variable=called_variable, star_list_variable=star_list_variable
            ),
            source_ref=internal_source_ref,
        )
    else:
        non_tuple_code = makeTryExceptSingleHandlerNode(
            tried=makeStatementAssignmentVariable(
                variable=star_list_variable,
                source=ExpressionBuiltinTuple(
                    value=ExpressionVariableRef(
                        variable=star_list_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                source_ref=internal_source_ref,
            ),
            exception_name="TypeError",
            handler_body=makeStarListArgumentErrorRaise(
                called_variable=called_variable, star_list_variable=star_list_variable
            ),
            source_ref=internal_source_ref,
        )

    return makeStatementConditional(
        condition=ExpressionComparisonIsNot(
            left=ExpressionBuiltinType1(
                value=ExpressionVariableRef(
                    variable=star_list_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            right=makeExpressionBuiltinTypeRef(
                builtin_name="tuple", source_ref=internal_source_ref
            ),
            source_ref=internal_source_ref,
        ),
        yes_branch=non_tuple_code,
        no_branch=None,
        source_ref=internal_source_ref,
    )


def _makeRaiseExceptionMustBeMapping(called_variable, star_dict_variable):
    return StatementRaiseException(
        exception_type=ExpressionBuiltinMakeException(
            exception_name="TypeError",
            args=(
                makeBinaryOperationNode(
                    operator="Mod",
                    left=makeConstantRefNode(
                        constant="""\
%s argument after ** must be a mapping, not %s""",
                        source_ref=internal_source_ref,
                        user_provided=True,
                    ),
                    right=makeExpressionMakeTuple(
                        elements=(
                            makeExpressionFunctionCall(
                                function=makeExpressionFunctionCreation(
                                    function_ref=ExpressionFunctionRef(
                                        function_body=getCallableNameDescBody(),
                                        source_ref=internal_source_ref,
                                    ),
                                    defaults=(),
                                    kw_defaults=None,
                                    annotations=None,
                                    source_ref=internal_source_ref,
                                ),
                                values=(
                                    ExpressionVariableRef(
                                        variable=called_variable,
                                        source_ref=internal_source_ref,
                                    ),
                                ),
                                source_ref=internal_source_ref,
                            ),
                            _makeNameAttributeLookup(
                                ExpressionBuiltinType1(
                                    value=ExpressionVariableRef(
                                        variable=star_dict_variable,
                                        source_ref=internal_source_ref,
                                    ),
                                    source_ref=internal_source_ref,
                                )
                            ),
                        ),
                        source_ref=internal_source_ref,
                    ),
                    source_ref=internal_source_ref,
                ),
            ),
            source_ref=internal_source_ref,
        ),
        exception_value=None,
        exception_trace=None,
        exception_cause=None,
        source_ref=internal_source_ref,
    )


def _makeIteratingLoopStatement(tmp_iter_variable, tmp_item_variable, statements):
    loop_body = makeStatementsSequenceFromStatements(
        makeTryExceptSingleHandlerNode(
            tried=makeStatementAssignmentVariable(
                variable=tmp_item_variable,
                source=ExpressionBuiltinNext1(
                    value=ExpressionTempVariableRef(
                        variable=tmp_iter_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                source_ref=internal_source_ref,
            ),
            exception_name="StopIteration",
            handler_body=StatementLoopBreak(source_ref=internal_source_ref),
            source_ref=internal_source_ref,
        ),
        *statements
    )

    return StatementLoop(loop_body=loop_body, source_ref=internal_source_ref)


def _makeStarDictArgumentToDictStatement(result, called_variable, star_dict_variable):
    temp_scope = result.allocateTempScope("mapping")

    tmp_dict_variable = result.allocateTempVariable(
        temp_scope, "dict", temp_type="object"
    )
    tmp_iter_variable = result.allocateTempVariable(
        temp_scope, "iter", temp_type="object"
    )
    tmp_keys_variable = result.allocateTempVariable(
        temp_scope, "keys", temp_type="object"
    )
    tmp_key_variable = result.allocateTempVariable(
        temp_scope, "key", temp_type="object"
    )

    loop_body = []

    if python_version >= 0x380:
        loop_body.append(
            makeStatementConditional(
                condition=ExpressionComparisonIn(
                    left=ExpressionTempVariableRef(
                        variable=tmp_key_variable, source_ref=internal_source_ref
                    ),
                    right=ExpressionVariableRef(
                        variable=tmp_dict_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                yes_branch=_makeRaiseDuplicationItem(
                    called_variable=called_variable, tmp_key_variable=tmp_key_variable
                ),
                no_branch=None,
                source_ref=internal_source_ref,
            )
        )

    loop_body.append(
        StatementDictOperationSet(
            dict_arg=ExpressionTempVariableRef(
                variable=tmp_dict_variable, source_ref=internal_source_ref
            ),
            key=ExpressionTempVariableRef(
                variable=tmp_key_variable, source_ref=internal_source_ref
            ),
            value=ExpressionSubscriptLookup(
                expression=ExpressionVariableRef(
                    variable=star_dict_variable, source_ref=internal_source_ref
                ),
                subscript=ExpressionTempVariableRef(
                    variable=tmp_key_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        )
    )

    mapping_case = makeStatementsSequenceFromStatements(
        makeTryExceptSingleHandlerNode(
            tried=makeStatementAssignmentVariable(
                variable=tmp_keys_variable,
                source=makeCallNode(
                    _makeNameAttributeLookup(
                        ExpressionVariableRef(
                            variable=star_dict_variable, source_ref=internal_source_ref
                        ),
                        attribute_name="keys",
                    ),
                    internal_source_ref,
                ),
                source_ref=internal_source_ref,
            ),
            exception_name="AttributeError",
            handler_body=_makeRaiseExceptionMustBeMapping(
                called_variable=called_variable, star_dict_variable=star_dict_variable
            ),
            source_ref=internal_source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=tmp_iter_variable,
            source=ExpressionBuiltinIter1(
                value=ExpressionTempVariableRef(
                    variable=tmp_keys_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=tmp_dict_variable,
            source=makeConstantRefNode(
                constant={}, source_ref=internal_source_ref, user_provided=True
            ),
            source_ref=internal_source_ref,
        ),
        _makeIteratingLoopStatement(
            tmp_iter_variable=tmp_iter_variable,
            tmp_item_variable=tmp_key_variable,
            statements=loop_body,
        ),
        makeStatementAssignmentVariable(
            variable=star_dict_variable,
            source=ExpressionTempVariableRef(
                variable=tmp_dict_variable, source_ref=internal_source_ref
            ),
            source_ref=internal_source_ref,
        ),
    )

    tried = makeStatementConditional(
        condition=ExpressionComparisonIsNot(
            left=ExpressionBuiltinType1(
                value=ExpressionVariableRef(
                    variable=star_dict_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            right=makeExpressionBuiltinTypeRef(
                builtin_name="dict", source_ref=internal_source_ref
            ),
            source_ref=internal_source_ref,
        ),
        yes_branch=mapping_case,
        no_branch=None,
        source_ref=internal_source_ref,
    )

    return makeTryFinallyStatement(
        provider=result,
        tried=tried,
        final=makeStatementsReleaseVariables(
            variables=(
                tmp_dict_variable,
                tmp_iter_variable,
                tmp_keys_variable,
                tmp_key_variable,
            ),
            source_ref=internal_source_ref,
        ),
        source_ref=internal_source_ref,
    )


def _makeRaiseNoStringItem(called_variable):
    if python_version < 0x390:
        raise_arg = makeBinaryOperationNode(
            operator="Mod",
            left=makeConstantRefNode(
                constant="%s keywords must be strings",
                source_ref=internal_source_ref,
                user_provided=True,
            ),
            right=makeExpressionFunctionCall(
                function=makeExpressionFunctionCreation(
                    function_ref=ExpressionFunctionRef(
                        function_body=getCallableNameDescBody(),
                        source_ref=internal_source_ref,
                    ),
                    defaults=(),
                    kw_defaults=None,
                    annotations=None,
                    source_ref=internal_source_ref,
                ),
                values=(
                    ExpressionVariableRef(
                        variable=called_variable, source_ref=internal_source_ref
                    ),
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        )
    else:
        raise_arg = makeConstantRefNode(
            constant="keywords must be strings",
            source_ref=internal_source_ref,
            user_provided=True,
        )

    return StatementRaiseException(
        exception_type=ExpressionBuiltinMakeException(
            exception_name="TypeError",
            args=(raise_arg,),
            source_ref=internal_source_ref,
        ),
        exception_value=None,
        exception_trace=None,
        exception_cause=None,
        source_ref=internal_source_ref,
    )


def _makeRaiseDuplicationItem(called_variable, tmp_key_variable):
    return StatementRaiseException(
        exception_type=ExpressionBuiltinMakeException(
            exception_name="TypeError",
            args=(
                makeBinaryOperationNode(
                    operator="Mod",
                    left=makeConstantRefNode(
                        constant="""\
%s got multiple values for keyword argument '%s'""",
                        source_ref=internal_source_ref,
                        user_provided=True,
                    ),
                    right=makeExpressionMakeTuple(
                        elements=(
                            makeExpressionFunctionCall(
                                function=makeExpressionFunctionCreation(
                                    function_ref=ExpressionFunctionRef(
                                        function_body=getCallableNameDescBody(),
                                        source_ref=internal_source_ref,
                                    ),
                                    defaults=(),
                                    kw_defaults=None,
                                    annotations=None,
                                    source_ref=internal_source_ref,
                                ),
                                values=(
                                    ExpressionVariableRef(
                                        variable=called_variable,
                                        source_ref=internal_source_ref,
                                    ),
                                ),
                                source_ref=internal_source_ref,
                            ),
                            ExpressionTempVariableRef(
                                variable=tmp_key_variable,
                                source_ref=internal_source_ref,
                            ),
                        ),
                        source_ref=internal_source_ref,
                    ),
                    source_ref=internal_source_ref,
                ),
            ),
            source_ref=internal_source_ref,
        ),
        exception_value=None,
        exception_trace=None,
        exception_cause=None,
        source_ref=internal_source_ref,
    )


def _makeStarDictArgumentMergeToKwStatement(
    result, called_variable, kw_variable, star_dict_variable
):
    # This is plain terribly complex
    temp_scope = result.allocateTempScope("dict")

    tmp_iter_variable = result.allocateTempVariable(
        temp_scope, "iter", temp_type="object"
    )
    tmp_keys_variable = result.allocateTempVariable(
        temp_scope, "keys", temp_type="object"
    )
    tmp_key_variable = result.allocateTempVariable(
        temp_scope, "key_xxx", temp_type="object"
    )

    tmp_variables = [tmp_iter_variable, tmp_keys_variable, tmp_key_variable]
    mapping_loop_body = (
        makeStatementConditional(
            condition=ExpressionComparisonIn(
                left=ExpressionTempVariableRef(
                    variable=tmp_key_variable, source_ref=internal_source_ref
                ),
                right=ExpressionVariableRef(
                    variable=kw_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            yes_branch=_makeRaiseDuplicationItem(
                called_variable=called_variable, tmp_key_variable=tmp_key_variable
            ),
            no_branch=None,
            source_ref=internal_source_ref,
        ),
        StatementAssignmentSubscript(
            subscribed=ExpressionVariableRef(
                variable=kw_variable, source_ref=internal_source_ref
            ),
            subscript=ExpressionTempVariableRef(
                variable=tmp_key_variable, source_ref=internal_source_ref
            ),
            source=ExpressionSubscriptLookup(
                expression=ExpressionVariableRef(
                    variable=star_dict_variable, source_ref=internal_source_ref
                ),
                subscript=ExpressionTempVariableRef(
                    variable=tmp_key_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    mapping_case = makeStatementsSequenceFromStatements(
        makeTryExceptSingleHandlerNode(
            tried=makeStatementAssignmentVariable(
                variable=tmp_keys_variable,
                source=makeCallNode(
                    _makeNameAttributeLookup(
                        ExpressionVariableRef(
                            variable=star_dict_variable, source_ref=internal_source_ref
                        ),
                        attribute_name="keys",
                    ),
                    internal_source_ref,
                ),
                source_ref=internal_source_ref,
            ),
            exception_name="AttributeError",
            handler_body=_makeRaiseExceptionMustBeMapping(
                called_variable=called_variable, star_dict_variable=star_dict_variable
            ),
            source_ref=internal_source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=tmp_iter_variable,
            source=ExpressionBuiltinIter1(
                value=ExpressionTempVariableRef(
                    variable=tmp_keys_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
        _makeIteratingLoopStatement(
            tmp_iter_variable=tmp_iter_variable,
            tmp_item_variable=tmp_key_variable,
            statements=mapping_loop_body,
        ),
    )

    temp_scope = result.allocateTempScope("dict")

    tmp_iter_variable = result.allocateTempVariable(
        temp_scope, "iter", temp_type="object"
    )
    tmp_item_variable = result.allocateTempVariable(
        temp_scope, "item", temp_type="object"
    )
    tmp_key_variable = result.allocateTempVariable(
        temp_scope, "key", temp_type="object"
    )

    tmp_variables += [tmp_iter_variable, tmp_item_variable, tmp_key_variable]
    dict_loop_body = (
        makeStatementAssignmentVariable(
            variable=tmp_key_variable,
            source=ExpressionSubscriptLookup(
                expression=ExpressionTempVariableRef(
                    variable=tmp_item_variable, source_ref=internal_source_ref
                ),
                subscript=makeConstantRefNode(
                    constant=0, source_ref=internal_source_ref, user_provided=True
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
        makeStatementConditional(
            condition=ExpressionComparisonIn(
                left=ExpressionTempVariableRef(
                    variable=tmp_key_variable, source_ref=internal_source_ref
                ),
                right=ExpressionVariableRef(
                    variable=kw_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            yes_branch=_makeRaiseDuplicationItem(
                called_variable=called_variable, tmp_key_variable=tmp_key_variable
            ),
            no_branch=None,
            source_ref=internal_source_ref,
        ),
        StatementAssignmentSubscript(
            subscribed=ExpressionVariableRef(
                variable=kw_variable, source_ref=internal_source_ref
            ),
            subscript=ExpressionTempVariableRef(
                variable=tmp_key_variable, source_ref=internal_source_ref
            ),
            source=ExpressionSubscriptLookup(
                expression=ExpressionTempVariableRef(
                    variable=tmp_item_variable, source_ref=internal_source_ref
                ),
                subscript=makeConstantRefNode(
                    constant=1, source_ref=internal_source_ref, user_provided=True
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    dict_case = makeStatementsSequenceFromStatements(
        makeStatementAssignmentVariable(
            variable=kw_variable,
            source=ExpressionBuiltinDict(
                pos_arg=ExpressionVariableRef(
                    variable=kw_variable, source_ref=internal_source_ref
                ),
                pairs=(),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=tmp_iter_variable,
            source=ExpressionBuiltinIter1(
                value=ExpressionDictOperationIteritems(
                    dict_arg=ExpressionVariableRef(
                        variable=star_dict_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
        _makeIteratingLoopStatement(
            tmp_iter_variable=tmp_iter_variable,
            tmp_item_variable=tmp_item_variable,
            statements=dict_loop_body,
        ),
    )

    dict_case = makeStatementConditional(
        condition=ExpressionVariableRef(
            variable=star_dict_variable, source_ref=internal_source_ref
        ),
        yes_branch=dict_case,
        no_branch=None,
        source_ref=internal_source_ref,
    )

    tried = makeStatementConditional(
        condition=ExpressionComparisonIsNot(
            left=ExpressionBuiltinType1(
                value=ExpressionVariableRef(
                    variable=star_dict_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            right=makeExpressionBuiltinTypeRef(
                builtin_name="dict", source_ref=internal_source_ref
            ),
            source_ref=internal_source_ref,
        ),
        yes_branch=mapping_case,
        no_branch=dict_case,
        source_ref=internal_source_ref,
    )

    return makeTryFinallyStatement(
        provider=result,
        tried=tried,
        final=makeStatementsReleaseVariables(
            variables=tmp_variables,
            source_ref=internal_source_ref,
        ),
        source_ref=internal_source_ref,
    )


@once_decorator
def getFunctionCallHelperStarList():
    helper_name = "complex_call_helper_star_list"
    # Equivalent of:
    #
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call.
    #
    # if not isinstance(star_arg_list, tuple):
    #     try:
    #         star_arg_list = tuple(star_arg_list)
    #     except TypeError:
    #         raise TypeError, "%s argument after * must be a sequence, not %s" % (
    #             get_callable_name_desc(function),
    #             type(star_arg_list).__name__
    #         )
    #
    # return called(*star_arg_list)

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=("called", "star_arg_list"),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")
    star_arg_list_variable = result.getVariableForAssignment(
        variable_name="star_arg_list"
    )

    body = makeStatementsSequenceFromStatements(
        _makeStarListArgumentToTupleStatement(
            called_variable=called_variable, star_list_variable=star_arg_list_variable
        ),
        StatementReturn(
            expression=makeExpressionCall(
                called=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                args=ExpressionVariableRef(
                    variable=star_arg_list_variable, source_ref=internal_source_ref
                ),
                kw=None,
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    result.setChildBody(body)

    return result


@once_decorator
def getFunctionCallHelperKeywordsStarList():
    helper_name = "complex_call_helper_keywords_star_list"

    # Equivalent of:
    #
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call.
    #
    # if not isinstance(star_arg_list, tuple):
    #     try:
    #         star_arg_list = tuple(star_arg_list)
    #     except TypeError:
    #         raise TypeError, "%s argument after * must be a sequence, not %s" % (
    #             get_callable_name_desc(function),
    #             type(star_arg_list).__name__
    #         )
    #
    # return called(*star_arg_list)

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=orderArgs("called", "kw", "star_arg_list"),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")

    kw_variable = result.getVariableForAssignment(variable_name="kw")

    star_arg_list_variable = result.getVariableForAssignment(
        variable_name="star_arg_list"
    )

    body = makeStatementsSequenceFromStatements(
        _makeStarListArgumentToTupleStatement(
            called_variable=called_variable, star_list_variable=star_arg_list_variable
        ),
        StatementReturn(
            expression=makeExpressionCall(
                called=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                args=ExpressionVariableRef(
                    variable=star_arg_list_variable, source_ref=internal_source_ref
                ),
                kw=ExpressionVariableRef(
                    variable=kw_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    result.setChildBody(body)

    return result


@once_decorator
def getFunctionCallHelperPosStarList():
    helper_name = "complex_call_helper_pos_star_list"

    # Equivalent of:
    #
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call.
    #
    # if not isinstance(star_arg_list, tuple):
    #     try:
    #         star_arg_list = tuple(star_arg_list)
    #     except TypeError:
    #         raise TypeError, "%s argument after * must be a sequence, not %s" % (
    #             get_callable_name_desc(function),
    #             type(star_arg_list).__name__
    #         )
    #
    # return called(*star_arg_list)

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=("called", "args", "star_arg_list"),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")

    args_variable = result.getVariableForAssignment(variable_name="args")

    star_arg_list_variable = result.getVariableForAssignment(
        variable_name="star_arg_list"
    )

    body = makeStatementsSequenceFromStatements(
        _makeStarListArgumentToTupleStatement(
            called_variable=called_variable, star_list_variable=star_arg_list_variable
        ),
        StatementReturn(
            expression=makeExpressionCall(
                called=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                args=makeBinaryOperationNode(
                    operator="Add",
                    left=ExpressionVariableRef(
                        variable=args_variable, source_ref=internal_source_ref
                    ),
                    right=ExpressionVariableRef(
                        variable=star_arg_list_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                kw=None,
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    result.setChildBody(body)

    return result


@once_decorator
def getFunctionCallHelperPosKeywordsStarList():
    helper_name = "complex_call_helper_pos_keywords_star_list"
    # Equivalent of:
    #
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call.
    #
    # if not isinstance(star_arg_list, tuple):
    #     try:
    #         star_arg_list = tuple(star_arg_list)
    #     except TypeError:
    #         raise TypeError, "%s argument after * must be a sequence, not %s" % (
    #             get_callable_name_desc(function),
    #             type(star_arg_list).__name__
    #         )
    #
    # return called(*star_arg_list)

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=orderArgs("called", "args", "kw", "star_arg_list"),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")

    args_variable = result.getVariableForAssignment(variable_name="args")

    kw_variable = result.getVariableForAssignment(variable_name="kw")

    star_arg_list_variable = result.getVariableForAssignment(
        variable_name="star_arg_list"
    )

    body = makeStatementsSequenceFromStatements(
        _makeStarListArgumentToTupleStatement(
            called_variable=called_variable, star_list_variable=star_arg_list_variable
        ),
        StatementReturn(
            expression=makeExpressionCall(
                called=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                args=makeBinaryOperationNode(
                    operator="Add",
                    left=ExpressionVariableRef(
                        variable=args_variable, source_ref=internal_source_ref
                    ),
                    right=ExpressionVariableRef(
                        variable=star_arg_list_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                kw=ExpressionVariableRef(
                    variable=kw_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    result.setChildBody(body)

    return result


@once_decorator
def getFunctionCallHelperStarDict():
    helper_name = "complex_call_helper_star_dict"
    # Equivalent of:
    #
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call.
    #
    # if not isinstance(star_arg_dict, dict):
    #     try:
    #         tmp_keys =  star_arg_dict.keys()
    #     except AttributeError:
    #         raise TypeError, ""%s argument after ** must be a mapping, not %s" % (
    #             get_callable_name_desc(function),
    #             type(star_arg_dict).__name__
    #         )
    #
    #     tmp_iter = iter(keys)
    #     tmp_dict = {}
    #
    #     while 1:
    #         try:
    #             tmp_key = tmp_iter.next()
    #         except StopIteration:
    #             break
    #
    #         tmp_dict[tmp_key] = star_dict_arg[tmp_key]
    #
    #     star_arg_dict = new
    #
    # return called(**star_arg_dict)

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=("called", "star_arg_dict"),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")

    star_arg_dict_variable = result.getVariableForAssignment(
        variable_name="star_arg_dict"
    )

    body = makeStatementsSequenceFromStatements(
        _makeStarDictArgumentToDictStatement(
            result=result,
            called_variable=called_variable,
            star_dict_variable=star_arg_dict_variable,
        ),
        StatementReturn(
            expression=makeExpressionCall(
                called=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                args=None,
                kw=ExpressionVariableRef(
                    variable=star_arg_dict_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    result.setChildBody(body)

    return result


@once_decorator
def getFunctionCallHelperPosStarDict():
    helper_name = "complex_call_helper_pos_star_dict"

    # Equivalent of:
    #
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call.
    #
    # if not isinstance(star_arg_dict, dict):
    #     try:
    #         tmp_keys =  star_arg_dict.keys()
    #     except AttributeError:
    #         raise TypeError, ""%s argument after ** must be a mapping, not %s" % (
    #             get_callable_name_desc(function),
    #             type(star_arg_dict).__name__
    #         )
    #
    #     tmp_iter = iter(keys)
    #     tmp_dict = {}
    #
    #     while 1:
    #         try:
    #             tmp_key = tmp_iter.next()
    #         except StopIteration:
    #             break
    #
    #         tmp_dict[tmp_key] = star_dict_arg[tmp_key]
    #
    #     star_arg_dict = new
    #
    # return called(args, **star_arg_dict)

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=("called", "args", "star_arg_dict"),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")

    args_variable = result.getVariableForAssignment(variable_name="args")

    star_arg_dict_variable = result.getVariableForAssignment(
        variable_name="star_arg_dict"
    )

    body = makeStatementsSequenceFromStatements(
        _makeStarDictArgumentToDictStatement(
            result=result,
            called_variable=called_variable,
            star_dict_variable=star_arg_dict_variable,
        ),
        StatementReturn(
            expression=makeExpressionCall(
                called=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                args=ExpressionVariableRef(
                    variable=args_variable, source_ref=internal_source_ref
                ),
                kw=ExpressionVariableRef(
                    variable=star_arg_dict_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    result.setChildBody(body)

    return result


@once_decorator
def getFunctionCallHelperKeywordsStarDict():
    helper_name = "complex_call_helper_keywords_star_dict"
    # Equivalent of:
    #
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call. One goal is to avoid copying "kw" unless really
    # necessary, and to take the slow route only for non-dictionaries.
    #
    # if not isinstance(star_arg_dict, dict):
    #     try:
    #         tmp_keys =  star_arg_dict.keys()
    #     except AttributeError:
    #         raise TypeError, ""%s argument after ** must be a mapping, not %s" % (
    #             get_callable_name_desc(function),
    #             type(star_arg_dict).__name__
    #         )
    #
    #     if keys:
    #         kw = dict(kw)
    #
    #         tmp_iter = iter(keys)
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
    #                     get_callable_name_desc(function),
    #                     tmp_key
    #                 )
    #
    #             kw[tmp_key] = star_dict_arg[tmp_key)
    #
    # elif star_arg_dict:
    #    tmp_iter = star_arg_dict.iteritems()
    #
    #    kw = dict(kw)
    #    while 1:
    #        try:
    #            tmp_key, tmp_value = tmp_iter.next()
    #        except StopIteration:
    #            break
    #
    #        if tmp_key in kw:
    #            raise TypeError, "%s got multiple values for keyword argument '%s'" % (
    #                 get_callable_name_desc(function),
    #                 tmp_key
    #            )
    #
    #        kw[tmp_key] = tmp_value
    #
    # return called(**kw)

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=("called", "kw", "star_arg_dict"),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")

    kw_variable = result.getVariableForAssignment(variable_name="kw")

    star_arg_dict_variable = result.getVariableForAssignment(
        variable_name="star_arg_dict"
    )

    body = makeStatementsSequenceFromStatements(
        _makeStarDictArgumentMergeToKwStatement(
            result=result,
            called_variable=called_variable,
            kw_variable=kw_variable,
            star_dict_variable=star_arg_dict_variable,
        ),
        StatementReturn(
            expression=makeExpressionCall(
                called=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                args=None,
                kw=ExpressionVariableRef(
                    variable=kw_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    result.setChildBody(body)

    return result


@once_decorator
def getFunctionCallHelperPosKeywordsStarDict():
    helper_name = "complex_call_helper_pos_keywords_star_dict"
    # Equivalent of:
    #
    # Note: Call in here is not the same, as it can go without checks directly
    # to PyObject_Call. One goal is to avoid copying "kw" unless really
    # necessary, and to take the slow route only for non-dictionaries.
    #
    # if not isinstance(star_arg_dict, dict):
    #     try:
    #         tmp_keys =  star_arg_dict.keys()
    #     except AttributeError:
    #         raise TypeError, ""%s argument after ** must be a mapping, not %s" % (
    #             get_callable_name_desc(function),
    #             type(star_arg_dict).__name__
    #         )
    #
    #     if keys:
    #         kw = dict(kw)
    #
    #         tmp_iter = iter(keys)
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
    #                     get_callable_name_desc(function),
    #                     tmp_key
    #                 )
    #
    #             kw[tmp_key] = star_dict_arg[tmp_key]
    #
    # elif star_arg_dict:
    #    tmp_iter = star_arg_dict.iteritems()
    #
    #    kw = dict(kw)
    #    while 1:
    #        try:
    #            tmp_key, tmp_value = tmp_iter.next()
    #        except StopIteration:
    #            break
    #
    #        if tmp_key in kw:
    #            raise TypeError, "%s got multiple values for keyword argument '%s'" % (
    #                 get_callable_name_desc(function),
    #                 tmp_key
    #            )
    #
    #        kw[tmp_key] = tmp_value
    #
    # return called(**kw )

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=("called", "args", "kw", "star_arg_dict"),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")

    args_variable = result.getVariableForAssignment(variable_name="args")

    kw_variable = result.getVariableForAssignment(variable_name="kw")

    star_arg_dict_variable = result.getVariableForAssignment(
        variable_name="star_arg_dict"
    )

    body = makeStatementsSequenceFromStatements(
        _makeStarDictArgumentMergeToKwStatement(
            result=result,
            called_variable=called_variable,
            kw_variable=kw_variable,
            star_dict_variable=star_arg_dict_variable,
        ),
        StatementReturn(
            expression=makeExpressionCall(
                called=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                args=ExpressionVariableRef(
                    variable=args_variable, source_ref=internal_source_ref
                ),
                kw=ExpressionVariableRef(
                    variable=kw_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    result.setChildBody(body)

    return result


def getDoubleStarArgsConversion(
    result, called_variable, kw_variable, star_arg_list_variable, star_arg_dict_variable
):
    statements = []

    if kw_variable is not None:
        statements.append(
            _makeStarDictArgumentMergeToKwStatement(
                result=result,
                called_variable=called_variable,
                kw_variable=kw_variable,
                star_dict_variable=star_arg_dict_variable,
            )
        )
    else:
        statements.append(
            _makeStarDictArgumentToDictStatement(
                result=result,
                called_variable=called_variable,
                star_dict_variable=star_arg_dict_variable,
            )
        )

    statements.append(
        _makeStarListArgumentToTupleStatement(
            called_variable=called_variable, star_list_variable=star_arg_list_variable
        )
    )

    return statements


@once_decorator
def getFunctionCallHelperStarListStarDict():
    helper_name = "complex_call_helper_star_list_star_dict"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=("called", "star_arg_list", "star_arg_dict"),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")

    star_arg_list_variable = result.getVariableForAssignment(
        variable_name="star_arg_list"
    )

    star_arg_dict_variable = result.getVariableForAssignment(
        variable_name="star_arg_dict"
    )

    statements = getDoubleStarArgsConversion(
        result=result,
        called_variable=called_variable,
        star_arg_list_variable=star_arg_list_variable,
        kw_variable=None,
        star_arg_dict_variable=star_arg_dict_variable,
    )

    statements.append(
        StatementReturn(
            expression=makeExpressionCall(
                called=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                args=ExpressionVariableRef(
                    variable=star_arg_list_variable, source_ref=internal_source_ref
                ),
                kw=ExpressionVariableRef(
                    variable=star_arg_dict_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        )
    )

    body = makeStatementsSequenceFromStatements(*statements)

    result.setChildBody(body)

    return result


@once_decorator
def getFunctionCallHelperPosStarListStarDict():
    helper_name = "complex_call_helper_pos_star_list_star_dict"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=("called", "args", "star_arg_list", "star_arg_dict"),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")

    args_variable = result.getVariableForAssignment(variable_name="args")

    star_arg_list_variable = result.getVariableForAssignment(
        variable_name="star_arg_list"
    )

    star_arg_dict_variable = result.getVariableForAssignment(
        variable_name="star_arg_dict"
    )

    statements = getDoubleStarArgsConversion(
        result=result,
        called_variable=called_variable,
        star_arg_list_variable=star_arg_list_variable,
        kw_variable=None,
        star_arg_dict_variable=star_arg_dict_variable,
    )

    if python_version >= 0x360:
        statements.reverse()

    statements.append(
        StatementReturn(
            expression=makeExpressionCall(
                called=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                args=makeBinaryOperationNode(
                    operator="Add",
                    left=ExpressionVariableRef(
                        variable=args_variable, source_ref=internal_source_ref
                    ),
                    right=ExpressionVariableRef(
                        variable=star_arg_list_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                kw=ExpressionVariableRef(
                    variable=star_arg_dict_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        )
    )

    body = makeStatementsSequenceFromStatements(*statements)

    result.setChildBody(body)

    return result


@once_decorator
def getFunctionCallHelperKeywordsStarListStarDict():
    helper_name = "complex_call_helper_keywords_star_list_star_dict"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=orderArgs("called", "kw", "star_arg_list", "star_arg_dict"),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")

    kw_variable = result.getVariableForAssignment(variable_name="kw")

    star_arg_list_variable = result.getVariableForAssignment(
        variable_name="star_arg_list"
    )

    star_arg_dict_variable = result.getVariableForAssignment(
        variable_name="star_arg_dict"
    )

    statements = getDoubleStarArgsConversion(
        result=result,
        called_variable=called_variable,
        star_arg_list_variable=star_arg_list_variable,
        kw_variable=kw_variable,
        star_arg_dict_variable=star_arg_dict_variable,
    )

    statements.append(
        StatementReturn(
            expression=makeExpressionCall(
                called=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                args=ExpressionVariableRef(
                    variable=star_arg_list_variable, source_ref=internal_source_ref
                ),
                kw=ExpressionVariableRef(
                    variable=kw_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        )
    )

    body = makeStatementsSequenceFromStatements(*statements)

    result.setChildBody(body)

    return result


@once_decorator
def getFunctionCallHelperPosKeywordsStarListStarDict():
    helper_name = "complex_call_helper_pos_keywords_star_list_star_dict"

    # Only need to check if the star argument value is a sequence and then
    # convert to tuple.
    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=orderArgs(
                "called", "args", "kw", "star_arg_list", "star_arg_dict"
            ),
            ps_list_star_arg=None,
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    called_variable = result.getVariableForAssignment(variable_name="called")

    args_variable = result.getVariableForAssignment(variable_name="args")

    kw_variable = result.getVariableForAssignment(variable_name="kw")

    star_arg_list_variable = result.getVariableForAssignment(
        variable_name="star_arg_list"
    )

    star_arg_dict_variable = result.getVariableForAssignment(
        variable_name="star_arg_dict"
    )

    statements = getDoubleStarArgsConversion(
        result=result,
        called_variable=called_variable,
        star_arg_list_variable=star_arg_list_variable,
        kw_variable=kw_variable,
        star_arg_dict_variable=star_arg_dict_variable,
    )

    if python_version >= 0x360:
        statements.reverse()

    statements.append(
        StatementReturn(
            expression=makeExpressionCall(
                called=ExpressionVariableRef(
                    variable=called_variable, source_ref=internal_source_ref
                ),
                args=makeBinaryOperationNode(
                    operator="Add",
                    left=ExpressionVariableRef(
                        variable=args_variable, source_ref=internal_source_ref
                    ),
                    right=ExpressionVariableRef(
                        variable=star_arg_list_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                kw=ExpressionVariableRef(
                    variable=kw_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        )
    )

    body = makeStatementsSequenceFromStatements(*statements)

    result.setChildBody(body)

    return result


@once_decorator
def getFunctionCallHelperDictionaryUnpacking():
    helper_name = "complex_call_helper_dict_unpacking_checks"

    result = makeInternalHelperFunctionBody(
        name=helper_name,
        parameters=ParameterSpec(
            ps_name=helper_name,
            ps_normal_args=("called",),
            ps_list_star_arg="args",
            ps_dict_star_arg=None,
            ps_default_count=0,
            ps_kw_only_args=(),
            ps_pos_only_args=(),
        ),
    )

    args_variable = result.getVariableForAssignment(variable_name="args")
    called_variable = result.getVariableForAssignment(variable_name="called")

    temp_scope = None

    tmp_result_variable = result.allocateTempVariable(
        temp_scope, "dict", temp_type="object"
    )
    tmp_iter_variable = result.allocateTempVariable(
        temp_scope, "dicts_iter", temp_type="object"
    )
    tmp_item_variable = result.allocateTempVariable(
        temp_scope, "args_item", temp_type="object"
    )
    tmp_iter2_variable = result.allocateTempVariable(
        temp_scope, "dict_iter", temp_type="object"
    )
    tmp_key_variable = result.allocateTempVariable(
        temp_scope, "dict_key", temp_type="object"
    )

    update_body = (
        makeStatementConditional(
            condition=ExpressionComparisonIsNot(
                left=ExpressionBuiltinType1(
                    value=ExpressionTempVariableRef(
                        variable=tmp_key_variable, source_ref=internal_source_ref
                    ),
                    source_ref=internal_source_ref,
                ),
                right=makeExpressionBuiltinTypeRef(
                    builtin_name="str", source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            yes_branch=_makeRaiseNoStringItem(called_variable=called_variable),
            no_branch=None,
            source_ref=internal_source_ref,
        ),
        makeStatementConditional(
            condition=ExpressionComparisonIn(
                left=ExpressionTempVariableRef(
                    variable=tmp_key_variable, source_ref=internal_source_ref
                ),
                right=ExpressionTempVariableRef(
                    variable=tmp_result_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            yes_branch=_makeRaiseDuplicationItem(
                called_variable=called_variable, tmp_key_variable=tmp_key_variable
            ),
            no_branch=None,
            source_ref=internal_source_ref,
        ),
        StatementDictOperationSetKeyValue(
            dict_arg=ExpressionTempVariableRef(
                variable=tmp_result_variable, source_ref=internal_source_ref
            ),
            key=ExpressionTempVariableRef(
                variable=tmp_key_variable, source_ref=internal_source_ref
            ),
            value=ExpressionSubscriptLookup(
                expression=ExpressionTempVariableRef(
                    variable=tmp_item_variable, source_ref=internal_source_ref
                ),
                subscript=ExpressionTempVariableRef(
                    variable=tmp_key_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
    )

    loop_body = (
        makeTryExceptSingleHandlerNode(
            tried=makeStatementsSequenceFromStatements(
                makeStatementAssignmentVariable(
                    variable=tmp_iter2_variable,
                    source=ExpressionBuiltinIter1(
                        value=makeCallNode(
                            _makeNameAttributeLookup(
                                ExpressionTempVariableRef(
                                    variable=tmp_item_variable,
                                    source_ref=internal_source_ref,
                                ),
                                attribute_name="keys",
                            ),
                            internal_source_ref,
                        ),
                        source_ref=internal_source_ref,
                    ),
                    source_ref=internal_source_ref,
                ),
                _makeIteratingLoopStatement(
                    tmp_iter_variable=tmp_iter2_variable,
                    tmp_item_variable=tmp_key_variable,
                    statements=update_body,
                ),
            ),
            exception_name="AttributeError",
            handler_body=_makeRaiseExceptionMustBeMapping(
                called_variable=called_variable, star_dict_variable=tmp_item_variable
            ),
            source_ref=internal_source_ref,
        ),
    )

    tried = makeStatementsSequenceFromStatements(
        makeStatementAssignmentVariable(
            variable=tmp_iter_variable,
            source=ExpressionBuiltinIter1(
                value=ExpressionVariableRef(
                    variable=args_variable, source_ref=internal_source_ref
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        ),
        makeStatementAssignmentVariable(
            variable=tmp_result_variable,
            source=makeConstantRefNode(constant={}, source_ref=internal_source_ref),
            source_ref=internal_source_ref,
        ),
        _makeIteratingLoopStatement(
            tmp_iter_variable=tmp_iter_variable,
            tmp_item_variable=tmp_item_variable,
            statements=loop_body,
        ),
        StatementReturn(
            expression=ExpressionTempVariableRef(
                variable=tmp_result_variable, source_ref=internal_source_ref
            ),
            source_ref=internal_source_ref,
        ),
    )

    body = makeStatementsSequenceFromStatement(
        makeTryFinallyStatement(
            provider=result,
            tried=tried,
            final=makeStatementsReleaseVariables(
                variables=(
                    tmp_result_variable,
                    tmp_iter_variable,
                    tmp_item_variable,
                    tmp_iter2_variable,
                    tmp_key_variable,
                ),
                source_ref=internal_source_ref,
            ),
            source_ref=internal_source_ref,
        )
    )

    result.setChildBody(body)

    return result
