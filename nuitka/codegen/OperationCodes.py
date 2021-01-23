#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Codes for operations.

There are unary and binary operations. Many of them have specializations and
of course types could play into it. Then there is also the added difficulty of
in-place assignments, which have other operation variants.
"""


from . import HelperDefinitions, OperatorCodes
from .CodeHelpers import (
    generateChildExpressionsCode,
    pickCodeHelper,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getTakeReferenceCode,
)


def generateOperationBinaryCode(to_name, expression, emit, context):
    left_arg_name, right_arg_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    # TODO: Decide and use one single spelling, inplace or in_place
    inplace = expression.isInplaceSuspect()

    _getBinaryOperationCode(
        to_name=to_name,
        expression=expression,
        operator=expression.getOperator(),
        arg_names=(left_arg_name, right_arg_name),
        in_place=inplace,
        emit=emit,
        context=context,
    )


def generateOperationNotCode(to_name, expression, emit, context):
    (arg_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    res_name = context.getIntResName()

    emit("%s = CHECK_IF_TRUE(%s);" % (res_name, arg_name))

    getErrorExitBoolCode(
        condition="%s == -1" % res_name,
        release_name=arg_name,
        needs_check=expression.subnode_operand.mayRaiseExceptionBool(BaseException),
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition="%s == 0" % res_name, emit=emit
    )


def generateOperationUnaryCode(to_name, expression, emit, context):
    (arg_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    _getUnaryOperationCode(
        to_name=to_name,
        expression=expression,
        operator=expression.getOperator(),
        arg_name=arg_name,
        needs_check=expression.mayRaiseException(BaseException),
        emit=emit,
        context=context,
    )


def _getBinaryOperationCode(
    to_name, expression, operator, arg_names, in_place, emit, context
):
    left = expression.subnode_left

    ref_count = 1
    needs_check = expression.mayRaiseExceptionOperation()

    helper = pickCodeHelper(
        prefix="BINARY_OPERATION_%s"
        % HelperDefinitions.getCodeNameForOperation(operator),
        suffix="INPLACE" if operator[0] == "I" else "",
        target_type=None if operator[0] == "I" else to_name.getCType(),
        left_shape=left.getTypeShape(),
        right_shape=expression.subnode_right.getTypeShape(),
        helpers=HelperDefinitions.getSpecializedOperations(operator),
        nonhelpers=HelperDefinitions.getNonSpecializedOperations(operator),
        source_ref=expression.source_ref,
    )

    # We must assume to write to a variable is "in_place" is active, not e.g.
    # a constant reference. That was asserted before calling us.
    if in_place or "INPLACE" in helper.helper_name:
        res_name = context.getBoolResName()

        # For module variable C type to reference later.
        if left.isExpressionVariableRef() and left.getVariable().isModuleVariable():
            emit("%s = %s;" % (context.getInplaceLeftName(), arg_names[0]))

        if (
            not left.isExpressionVariableRef()
            and not left.isExpressionTempVariableRef()
        ):
            if not context.needsCleanup(arg_names[0]):
                getTakeReferenceCode(arg_names[0], emit)

        emit("%s = %s(&%s, %s);" % (res_name, helper, arg_names[0], arg_names[1]))

        getErrorExitBoolCode(
            condition="%s == false" % res_name,
            release_names=arg_names,
            needs_check=needs_check,
            emit=emit,
            context=context,
        )

        emit("%s = %s;" % (to_name, arg_names[0]))

        if (
            not left.isExpressionVariableRef()
            and not left.isExpressionTempVariableRef()
        ):
            context.addCleanupTempName(to_name)
    else:
        helper.emitHelperCall(
            to_name=to_name,
            arg_names=arg_names,
            ref_count=ref_count,
            needs_check=needs_check,
            emit=emit,
            context=context,
        )


def _getUnaryOperationCode(
    to_name, expression, operator, arg_name, needs_check, emit, context
):
    impl_helper, ref_count = OperatorCodes.unary_operator_codes[operator]

    helper = "UNARY_OPERATION"
    prefix_args = (impl_helper,)

    with withObjectCodeTemporaryAssignment(
        to_name, "op_%s_res" % operator.lower(), expression, emit, context
    ) as value_name:

        emit(
            "%s = %s(%s);"
            % (
                value_name,
                helper,
                ", ".join(str(arg_name) for arg_name in prefix_args + (arg_name,)),
            )
        )

        getErrorExitCode(
            check_name=value_name,
            release_name=arg_name,
            needs_check=needs_check,
            emit=emit,
            context=context,
        )

        if ref_count:
            context.addCleanupTempName(value_name)
